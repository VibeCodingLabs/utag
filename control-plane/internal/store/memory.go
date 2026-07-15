package store

import (
	"context"
	"sort"
	"sync"
	"time"
)

// Memory: dev/test store. Same semantics as postgres impl.
type Memory struct {
	mu        sync.Mutex
	jobs      map[string]*Job
	events    map[string][]Event
	artifacts map[string]*Artifact
	byJob     map[string][]string
}

func NewMemory() *Memory {
	return &Memory{jobs: map[string]*Job{}, events: map[string][]Event{},
		artifacts: map[string]*Artifact{}, byJob: map[string][]string{}}
}

func (m *Memory) CreateJob(_ context.Context, j *Job) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	cp := *j
	m.jobs[j.ID] = &cp
	return nil
}

func (m *Memory) GetJob(_ context.Context, id string) (*Job, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	j, ok := m.jobs[id]
	if !ok {
		return nil, ErrNotFound
	}
	cp := *j
	return &cp, nil
}

func (m *Memory) ListJobs(_ context.Context, limit int) ([]Job, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var out []Job
	for _, j := range m.jobs {
		out = append(out, *j)
	}
	sort.Slice(out, func(a, b int) bool { return out[a].CreatedAt.After(out[b].CreatedAt) })
	if limit > 0 && len(out) > limit {
		out = out[:limit]
	}
	return out, nil
}

func (m *Memory) ClaimNext(_ context.Context) (*Job, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var queued []*Job
	for _, j := range m.jobs {
		if j.Status == StatusQueued {
			queued = append(queued, j)
		}
	}
	if len(queued) == 0 {
		return nil, ErrNotFound
	}
	sort.Slice(queued, func(a, b int) bool { return queued[a].CreatedAt.Before(queued[b].CreatedAt) })
	j := queued[0]
	j.Status = StatusRunning
	j.UpdatedAt = time.Now().UTC()
	cp := *j
	return &cp, nil
}

func (m *Memory) FinishJob(_ context.Context, id string, status JobStatus, errMsg string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	j, ok := m.jobs[id]
	if !ok {
		return ErrNotFound
	}
	j.Status, j.Error, j.UpdatedAt = status, errMsg, time.Now().UTC()
	return nil
}

func (m *Memory) AppendEvent(_ context.Context, e *Event) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	e.Seq = len(m.events[e.JobID]) + 1
	e.At = time.Now().UTC()
	m.events[e.JobID] = append(m.events[e.JobID], *e)
	return nil
}

func (m *Memory) Events(_ context.Context, jobID string, afterSeq int) ([]Event, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	all := m.events[jobID]
	var out []Event
	for _, e := range all {
		if e.Seq > afterSeq {
			out = append(out, e)
		}
	}
	return out, nil
}

func (m *Memory) AddArtifact(_ context.Context, a *Artifact) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	cp := *a
	m.artifacts[a.ID] = &cp
	m.byJob[a.JobID] = append(m.byJob[a.JobID], a.ID)
	return nil
}

func (m *Memory) Artifacts(_ context.Context, jobID string) ([]Artifact, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var out []Artifact
	for _, id := range m.byJob[jobID] {
		out = append(out, *m.artifacts[id])
	}
	return out, nil
}

func (m *Memory) GetArtifact(_ context.Context, id string) (*Artifact, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	a, ok := m.artifacts[id]
	if !ok {
		return nil, ErrNotFound
	}
	cp := *a
	return &cp, nil
}

func (m *Memory) Ping(context.Context) error { return nil }
