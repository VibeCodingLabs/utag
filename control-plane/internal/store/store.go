// Package store: job queue + artifact store behind one interface.
// Impls: memory (dev/tests) and postgres (SELECT ... FOR UPDATE SKIP LOCKED).
package store

import (
	"context"
	"errors"
	"time"
)

type JobStatus string

const (
	StatusQueued    JobStatus = "queued"
	StatusRunning   JobStatus = "running"
	StatusSucceeded JobStatus = "succeeded"
	StatusFailed    JobStatus = "failed"
)

type Job struct {
	ID        string    `json:"id"`
	Target    string    `json:"target"`
	Backend   string    `json:"backend"`
	InputKind string    `json:"input_kind"`
	Input     string    `json:"input"`
	Metadata  string    `json:"metadata,omitempty"`
	Status    JobStatus `json:"status"`
	Error     string    `json:"error,omitempty"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Event struct {
	JobID   string    `json:"job_id"`
	Seq     int       `json:"seq"`
	Type    string    `json:"type"`
	Payload string    `json:"payload"`
	At      time.Time `json:"at"`
}

type Artifact struct {
	ID      string `json:"id"`
	JobID   string `json:"job_id"`
	Path    string `json:"path"`
	Content string `json:"content"`
	Report  string `json:"report"` // ValidationReport JSON from the worker
}

var ErrNotFound = errors.New("not found")

type Store interface {
	CreateJob(ctx context.Context, j *Job) error
	GetJob(ctx context.Context, id string) (*Job, error)
	// ClaimNext atomically moves the oldest queued job to running.
	// Returns ErrNotFound when the queue is empty.
	ClaimNext(ctx context.Context) (*Job, error)
	FinishJob(ctx context.Context, id string, status JobStatus, errMsg string) error
	AppendEvent(ctx context.Context, e *Event) error
	Events(ctx context.Context, jobID string, afterSeq int) ([]Event, error)
	AddArtifact(ctx context.Context, a *Artifact) error
	Artifacts(ctx context.Context, jobID string) ([]Artifact, error)
	GetArtifact(ctx context.Context, id string) (*Artifact, error)
	Ping(ctx context.Context) error
}
