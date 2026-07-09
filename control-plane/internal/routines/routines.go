// Package routines: in-binary interval scheduler ("Claude Routines" analogue).
// Config-defined; each tick reads the input file and enqueues a job directly
// on the store. Interval-based by design (time.ParseDuration); cron-precision
// schedules belong to the k8s CronJob manifest in deploy/ (documented tradeoff
// — avoids a cron dependency until measured need).
package routines

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"time"

	"github.com/google/uuid"

	"utag/control-plane/internal/store"
)

type Routine struct {
	Name      string `mapstructure:"name" json:"name"`
	Every     string `mapstructure:"every" json:"every"` // e.g. "15m", "1h"
	Target    string `mapstructure:"target" json:"target"`
	InputKind string `mapstructure:"input-kind" json:"input_kind"`
	InputFile string `mapstructure:"input-file" json:"input_file"`
}

func Run(ctx context.Context, st store.Store, log *slog.Logger, rs []Routine) error {
	for _, r := range rs {
		d, err := time.ParseDuration(r.Every)
		if err != nil || d <= 0 {
			return fmt.Errorf("routine %q: bad interval %q", r.Name, r.Every)
		}
		go tick(ctx, st, log, r, d)
	}
	return nil
}

func tick(ctx context.Context, st store.Store, log *slog.Logger, r Routine, d time.Duration) {
	t := time.NewTicker(d)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			input, err := os.ReadFile(r.InputFile)
			if err != nil {
				log.Error("routine", "name", r.Name, "err", err.Error())
				continue
			}
			now := time.Now().UTC()
			kind := r.InputKind
			if kind == "" {
				kind = "prompt-yaml"
			}
			j := &store.Job{ID: uuid.NewString(), Target: r.Target, Backend: "routine",
				InputKind: kind, Input: string(input),
				Metadata:  fmt.Sprintf(`{"routine":%q}`, r.Name),
				Status:    store.StatusQueued, CreatedAt: now, UpdatedAt: now}
			if err := st.CreateJob(ctx, j); err != nil {
				log.Error("routine", "name", r.Name, "err", err.Error())
				continue
			}
			_ = st.AppendEvent(ctx, &store.Event{JobID: j.ID, Type: "queued",
				Payload: fmt.Sprintf(`{"source":"routine","name":%q}`, r.Name)})
			log.Info("routine", "name", r.Name, "job", j.ID)
		}
	}
}
