package routines

import (
	"context"
	"log/slog"
	"os"
	"path/filepath"
	"testing"
	"time"

	"utag/control-plane/internal/store"
)

func TestRoutineEnqueuesJobs(t *testing.T) {
	td := t.TempDir()
	f := filepath.Join(td, "in.yaml")
	os.WriteFile(f, []byte("version: '1.0'\nname: r\n"), 0o644)
	st := store.NewMemory()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	err := Run(ctx, st, slog.New(slog.NewTextHandler(os.Stderr, nil)),
		[]Routine{{Name: "nightly", Every: "30ms", Target: "openapi-3.1", InputFile: f}})
	if err != nil {
		t.Fatal(err)
	}
	deadline := time.After(3 * time.Second)
	for {
		if j, err := st.ClaimNext(ctx); err == nil {
			if j.Target != "openapi-3.1" || j.Backend != "routine" {
				t.Fatalf("wrong job: %+v", j)
			}
			return
		}
		select {
		case <-deadline:
			t.Fatal("routine never enqueued a job")
		case <-time.After(10 * time.Millisecond):
		}
	}
}

func TestBadIntervalRejected(t *testing.T) {
	if err := Run(context.Background(), store.NewMemory(),
		slog.New(slog.NewTextHandler(os.Stderr, nil)),
		[]Routine{{Name: "x", Every: "not-a-duration"}}); err == nil {
		t.Fatal("bad interval accepted")
	}
}
