package store

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Postgres: store + queue in one database. Claim uses
// SELECT ... FOR UPDATE SKIP LOCKED — the standard single-DB work queue.
type Postgres struct{ pool *pgxpool.Pool }

const schema = `
CREATE TABLE IF NOT EXISTS jobs (
  id text PRIMARY KEY, target text NOT NULL, backend text NOT NULL,
  input_kind text NOT NULL, input text NOT NULL,
  status text NOT NULL, error text NOT NULL DEFAULT '',
  metadata text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS metadata text NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS jobs_queued ON jobs (created_at) WHERE status = 'queued';
CREATE TABLE IF NOT EXISTS events (
  job_id text NOT NULL REFERENCES jobs(id), seq int NOT NULL,
  type text NOT NULL, payload text NOT NULL, at timestamptz NOT NULL,
  PRIMARY KEY (job_id, seq));
CREATE TABLE IF NOT EXISTS artifacts (
  id text PRIMARY KEY, job_id text NOT NULL REFERENCES jobs(id),
  path text NOT NULL, content text NOT NULL, report text NOT NULL DEFAULT '');`

func NewPostgres(ctx context.Context, url string) (*Postgres, error) {
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return nil, err
	}
	if _, err := pool.Exec(ctx, schema); err != nil {
		return nil, err
	}
	return &Postgres{pool: pool}, nil
}

func (p *Postgres) CreateJob(ctx context.Context, j *Job) error {
	_, err := p.pool.Exec(ctx,
		`INSERT INTO jobs (id,target,backend,input_kind,input,metadata,status,created_at,updated_at)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
		j.ID, j.Target, j.Backend, j.InputKind, j.Input, j.Metadata, j.Status, j.CreatedAt, j.UpdatedAt)
	return err
}

func (p *Postgres) GetJob(ctx context.Context, id string) (*Job, error) {
	var j Job
	err := p.pool.QueryRow(ctx,
		`SELECT id,target,backend,input_kind,input,metadata,status,error,created_at,updated_at
		 FROM jobs WHERE id=$1`, id).
		Scan(&j.ID, &j.Target, &j.Backend, &j.InputKind, &j.Input, &j.Metadata, &j.Status, &j.Error,
			&j.CreatedAt, &j.UpdatedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrNotFound
	}
	return &j, err
}

func (p *Postgres) ListJobs(ctx context.Context, limit int) ([]Job, error) {
	if limit <= 0 || limit > 500 {
		limit = 100
	}
	rows, err := p.pool.Query(ctx,
		`SELECT id,target,backend,input_kind,input,metadata,status,error,created_at,updated_at
		 FROM jobs ORDER BY created_at DESC LIMIT $1`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Job
	for rows.Next() {
		var j Job
		if err := rows.Scan(&j.ID, &j.Target, &j.Backend, &j.InputKind, &j.Input, &j.Metadata,
			&j.Status, &j.Error, &j.CreatedAt, &j.UpdatedAt); err != nil {
			return nil, err
		}
		out = append(out, j)
	}
	return out, rows.Err()
}

func (p *Postgres) ClaimNext(ctx context.Context) (*Job, error) {
	tx, err := p.pool.Begin(ctx)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback(ctx)
	var j Job
	err = tx.QueryRow(ctx,
		`SELECT id,target,backend,input_kind,input,metadata,status,error,created_at,updated_at
		 FROM jobs WHERE status='queued' ORDER BY created_at
		 FOR UPDATE SKIP LOCKED LIMIT 1`).
		Scan(&j.ID, &j.Target, &j.Backend, &j.InputKind, &j.Input, &j.Metadata, &j.Status, &j.Error,
			&j.CreatedAt, &j.UpdatedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	now := time.Now().UTC()
	if _, err := tx.Exec(ctx, `UPDATE jobs SET status='running', updated_at=$2 WHERE id=$1`,
		j.ID, now); err != nil {
		return nil, err
	}
	if err := tx.Commit(ctx); err != nil {
		return nil, err
	}
	j.Status, j.UpdatedAt = StatusRunning, now
	return &j, nil
}

func (p *Postgres) FinishJob(ctx context.Context, id string, status JobStatus, errMsg string) error {
	ct, err := p.pool.Exec(ctx,
		`UPDATE jobs SET status=$2, error=$3, updated_at=$4 WHERE id=$1`,
		id, status, errMsg, time.Now().UTC())
	if err == nil && ct.RowsAffected() == 0 {
		return ErrNotFound
	}
	return err
}

func (p *Postgres) AppendEvent(ctx context.Context, e *Event) error {
	_, err := p.pool.Exec(ctx,
		`INSERT INTO events (job_id, seq, type, payload, at)
		 VALUES ($1, (SELECT coalesce(max(seq),0)+1 FROM events WHERE job_id=$1), $2, $3, now())`,
		e.JobID, e.Type, e.Payload)
	return err
}

func (p *Postgres) Events(ctx context.Context, jobID string, afterSeq int) ([]Event, error) {
	rows, err := p.pool.Query(ctx,
		`SELECT job_id,seq,type,payload,at FROM events WHERE job_id=$1 AND seq>$2 ORDER BY seq`,
		jobID, afterSeq)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Event
	for rows.Next() {
		var e Event
		if err := rows.Scan(&e.JobID, &e.Seq, &e.Type, &e.Payload, &e.At); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

func (p *Postgres) AddArtifact(ctx context.Context, a *Artifact) error {
	_, err := p.pool.Exec(ctx,
		`INSERT INTO artifacts (id,job_id,path,content,report) VALUES ($1,$2,$3,$4,$5)`,
		a.ID, a.JobID, a.Path, a.Content, a.Report)
	return err
}

func (p *Postgres) Artifacts(ctx context.Context, jobID string) ([]Artifact, error) {
	rows, err := p.pool.Query(ctx,
		`SELECT id,job_id,path,content,report FROM artifacts WHERE job_id=$1 ORDER BY path`, jobID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Artifact
	for rows.Next() {
		var a Artifact
		if err := rows.Scan(&a.ID, &a.JobID, &a.Path, &a.Content, &a.Report); err != nil {
			return nil, err
		}
		out = append(out, a)
	}
	return out, rows.Err()
}

func (p *Postgres) GetArtifact(ctx context.Context, id string) (*Artifact, error) {
	var a Artifact
	err := p.pool.QueryRow(ctx,
		`SELECT id,job_id,path,content,report FROM artifacts WHERE id=$1`, id).
		Scan(&a.ID, &a.JobID, &a.Path, &a.Content, &a.Report)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrNotFound
	}
	return &a, err
}

func (p *Postgres) Ping(ctx context.Context) error { return p.pool.Ping(ctx) }
