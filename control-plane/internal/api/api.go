// Package api: the hub. Every surface (CLI, GitHub App, Slack, Routines, workers)
// is a thin client of these endpoints. Go 1.22 ServeMux method+path patterns.
package api

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"

	"github.com/google/uuid"
	"golang.org/x/time/rate"

	gh "utag/control-plane/internal/github"
	"utag/control-plane/internal/store"
)

type Server struct {
	Store         store.Store
	Token         string // bearer; empty = dev mode (logged loudly)
	Log           *slog.Logger
	limiters      *rate.Limiter
	WebhookSecret string        // GitHub App webhook secret ("" = adapter off)
	GitHub        *gh.Deliverer // nil = delivery off
}

type createJobReq struct {
	Target    string `json:"target"`
	Backend   string `json:"backend"`
	InputKind string `json:"input_kind"`
	Input     string `json:"input"`
	Metadata  string `json:"metadata"`
}

type completeReq struct {
	Status    string `json:"status"` // succeeded | failed
	Error     string `json:"error"`
	Artifacts []struct {
		Path    string `json:"path"`
		Content string `json:"content"`
		Report  string `json:"report"`
	} `json:"artifacts"`
}

func New(s store.Store, token string, log *slog.Logger) *Server {
	return &Server{Store: s, Token: token, Log: log,
		limiters: rate.NewLimiter(rate.Limit(50), 100)} // 50 rps, burst 100
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", s.health)
	mux.HandleFunc("POST /v1/jobs", s.auth(s.createJob))
	mux.HandleFunc("GET /v1/jobs/{id}", s.auth(s.getJob))
	mux.HandleFunc("GET /v1/jobs/{id}/events", s.auth(s.streamEvents))
	mux.HandleFunc("GET /v1/jobs/{id}/artifacts", s.auth(s.listArtifacts))
	mux.HandleFunc("GET /v1/artifacts/{id}", s.auth(s.getArtifact))
	mux.HandleFunc("POST /v1/worker/claim", s.auth(s.claim))
	mux.HandleFunc("POST /v1/integrations/github/webhook", s.githubWebhook) // HMAC-authed, not bearer
	mux.HandleFunc("POST /v1/jobs/{id}/complete", s.auth(s.complete))
	return s.trace(mux)
}

// trace: request-scoped trace_id in logs + response header (OTel-exporter-ready shape).
func (s *Server) trace(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		tid := uuid.NewString()
		w.Header().Set("X-Trace-Id", tid)
		start := time.Now()
		next.ServeHTTP(w, r)
		s.Log.Info("http", "trace_id", tid, "method", r.Method, "path", r.URL.Path,
			"dur_ms", time.Since(start).Milliseconds())
	})
}

func (s *Server) auth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if !s.limiters.Allow() {
			http.Error(w, `{"error":"rate limited"}`, http.StatusTooManyRequests)
			return
		}
		if s.Token != "" && r.Header.Get("Authorization") != "Bearer "+s.Token {
			http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}

func (s *Server) health(w http.ResponseWriter, r *http.Request) {
	if err := s.Store.Ping(r.Context()); err != nil {
		http.Error(w, `{"status":"degraded"}`, http.StatusServiceUnavailable)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) createJob(w http.ResponseWriter, r *http.Request) {
	var req createJobReq
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<20)).Decode(&req); err != nil {
		httpErr(w, http.StatusBadRequest, err)
		return
	}
	if req.Target == "" || req.Input == "" {
		httpErr(w, http.StatusUnprocessableEntity, errors.New("target and input required"))
		return
	}
	now := time.Now().UTC()
	j := &store.Job{ID: uuid.NewString(), Target: req.Target, Backend: req.Backend,
		InputKind: req.InputKind, Input: req.Input, Metadata: req.Metadata, Status: store.StatusQueued,
		CreatedAt: now, UpdatedAt: now}
	if err := s.Store.CreateJob(r.Context(), j); err != nil {
		httpErr(w, http.StatusInternalServerError, err)
		return
	}
	_ = s.Store.AppendEvent(r.Context(), &store.Event{JobID: j.ID, Type: "queued", Payload: "{}"})
	writeJSON(w, http.StatusCreated, j)
}

func (s *Server) getJob(w http.ResponseWriter, r *http.Request) {
	j, err := s.Store.GetJob(r.Context(), r.PathValue("id"))
	if err != nil {
		notFoundOr500(w, err)
		return
	}
	writeJSON(w, http.StatusOK, j)
}

func (s *Server) claim(w http.ResponseWriter, r *http.Request) {
	j, err := s.Store.ClaimNext(r.Context())
	if errors.Is(err, store.ErrNotFound) {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if err != nil {
		httpErr(w, http.StatusInternalServerError, err)
		return
	}
	_ = s.Store.AppendEvent(r.Context(), &store.Event{JobID: j.ID, Type: "claimed", Payload: "{}"})
	writeJSON(w, http.StatusOK, j)
}

func (s *Server) complete(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	var req completeReq
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<20)).Decode(&req); err != nil {
		httpErr(w, http.StatusBadRequest, err)
		return
	}
	status := store.StatusSucceeded
	if req.Status == "failed" {
		status = store.StatusFailed
	}
	for _, a := range req.Artifacts {
		if err := s.Store.AddArtifact(r.Context(), &store.Artifact{
			ID: uuid.NewString(), JobID: id, Path: a.Path, Content: a.Content, Report: a.Report,
		}); err != nil {
			httpErr(w, http.StatusInternalServerError, err)
			return
		}
	}
	if err := s.Store.FinishJob(r.Context(), id, status, req.Error); err != nil {
		notFoundOr500(w, err)
		return
	}
	_ = s.Store.AppendEvent(r.Context(), &store.Event{JobID: id, Type: string(status), Payload: "{}"})
	if s.GitHub != nil && status == store.StatusSucceeded {
		if job, err := s.Store.GetJob(r.Context(), id); err == nil && job.Metadata != "" {
			arts, _ := s.Store.Artifacts(r.Context(), id)
			go s.deliverGitHub(job, arts) // async; outcome recorded as job events
		}
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": string(status)})
}

func (s *Server) listArtifacts(w http.ResponseWriter, r *http.Request) {
	arts, err := s.Store.Artifacts(r.Context(), r.PathValue("id"))
	if err != nil {
		httpErr(w, http.StatusInternalServerError, err)
		return
	}
	writeJSON(w, http.StatusOK, arts)
}

func (s *Server) getArtifact(w http.ResponseWriter, r *http.Request) {
	a, err := s.Store.GetArtifact(r.Context(), r.PathValue("id"))
	if err != nil {
		notFoundOr500(w, err)
		return
	}
	writeJSON(w, http.StatusOK, a)
}

// streamEvents: SSE via store polling (500ms). Postgres LISTEN/NOTIFY later if measured need.
func (s *Server) streamEvents(w http.ResponseWriter, r *http.Request) {
	fl, ok := w.(http.Flusher)
	if !ok {
		httpErr(w, http.StatusInternalServerError, errors.New("streaming unsupported"))
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	id, after := r.PathValue("id"), 0
	tick := time.NewTicker(500 * time.Millisecond)
	defer tick.Stop()
	for {
		evs, err := s.Store.Events(r.Context(), id, after)
		if err != nil {
			return
		}
		terminal := false
		for _, e := range evs {
			b, _ := json.Marshal(e)
			fmt.Fprintf(w, "event: %s\ndata: %s\n\n", e.Type, b)
			after = e.Seq
			if e.Type == string(store.StatusSucceeded) || e.Type == string(store.StatusFailed) {
				terminal = true
			}
		}
		fl.Flush()
		if terminal {
			return
		}
		select {
		case <-r.Context().Done():
			return
		case <-tick.C:
		}
	}
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func httpErr(w http.ResponseWriter, code int, err error) {
	writeJSON(w, code, map[string]string{"error": err.Error()})
}

func notFoundOr500(w http.ResponseWriter, err error) {
	if errors.Is(err, store.ErrNotFound) {
		httpErr(w, http.StatusNotFound, err)
		return
	}
	httpErr(w, http.StatusInternalServerError, err)
}

func (s *Server) deliverGitHub(job *store.Job, arts []store.Artifact) {
	ctx := context.Background()
	url, err := s.GitHub.Deliver(job, arts)
	if err != nil {
		s.Log.Error("github-deliver", "job", job.ID, "err", err.Error())
		_ = s.Store.AppendEvent(ctx, &store.Event{JobID: job.ID, Type: "delivery_failed",
			Payload: fmt.Sprintf("{\"error\":%q}", err.Error())})
		return
	}
	s.Log.Info("github-deliver", "job", job.ID, "pr", url)
	_ = s.Store.AppendEvent(ctx, &store.Event{JobID: job.ID, Type: "pr_opened",
		Payload: fmt.Sprintf("{\"url\":%q}", url)})
}

// githubWebhook: HMAC-verified; "/utag generate <target> <path>" comments become jobs.
func (s *Server) githubWebhook(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 2<<20))
	if err != nil {
		httpErr(w, http.StatusBadRequest, err)
		return
	}
	if !gh.VerifySignature(s.WebhookSecret, r.Header.Get("X-Hub-Signature-256"), body) {
		httpErr(w, http.StatusUnauthorized, errors.New("bad signature"))
		return
	}
	if r.Header.Get("X-GitHub-Event") != "issue_comment" {
		writeJSON(w, http.StatusAccepted, map[string]string{"status": "ignored"})
		return
	}
	ev, err := gh.ParseCommentEvent(body)
	if err != nil || ev.Action != "created" {
		writeJSON(w, http.StatusAccepted, map[string]string{"status": "ignored"})
		return
	}
	cmd, ok := gh.ParseCommand(ev.Comment.Body)
	if !ok {
		writeJSON(w, http.StatusAccepted, map[string]string{"status": "no-command"})
		return
	}
	if s.GitHub == nil {
		httpErr(w, http.StatusServiceUnavailable, errors.New("github delivery not configured"))
		return
	}
	token, err := s.GitHub.Client.InstallationToken(ev.Installation.ID)
	if err != nil {
		httpErr(w, http.StatusBadGateway, err)
		return
	}
	input, err := s.GitHub.Client.FetchFile(token, ev.Repository.FullName, cmd.Path,
		ev.Repository.DefaultBranch)
	if err != nil {
		httpErr(w, http.StatusBadGateway, err)
		return
	}
	meta, _ := json.Marshal(gh.JobMeta{Repo: ev.Repository.FullName,
		InstallationID: ev.Installation.ID, BaseBranch: ev.Repository.DefaultBranch,
		IssueNumber: ev.Issue.Number, SourcePath: cmd.Path})
	now := time.Now().UTC()
	j := &store.Job{ID: uuid.NewString(), Target: cmd.Target, Backend: "worker",
		InputKind: "prompt-yaml", Input: input, Metadata: string(meta),
		Status: store.StatusQueued, CreatedAt: now, UpdatedAt: now}
	if err := s.Store.CreateJob(r.Context(), j); err != nil {
		httpErr(w, http.StatusInternalServerError, err)
		return
	}
	_ = s.Store.AppendEvent(r.Context(), &store.Event{JobID: j.ID, Type: "queued",
		Payload: fmt.Sprintf("{\"source\":\"github\",\"repo\":%q}", ev.Repository.FullName)})
	writeJSON(w, http.StatusAccepted, j)
}
