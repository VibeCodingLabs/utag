package cmd

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spf13/cobra"

	"utag/control-plane/internal/api"
	ghpkg "utag/control-plane/internal/github"
	"utag/control-plane/internal/routines"
	"utag/control-plane/internal/store"
)

var serveCmd = &cobra.Command{
	Use:   "serve",
	Short: "Run the control-plane job API",
	RunE: func(cmd *cobra.Command, args []string) error {
		log := slog.New(slog.NewJSONHandler(os.Stdout, nil)) // twelve-factor XI
		var st store.Store
		if settings.DatabaseURL != "" {
			pg, err := store.NewPostgres(cmd.Context(), settings.DatabaseURL)
			if err != nil {
				return fmt.Errorf("postgres: %w", err)
			}
			st = pg
			log.Info("store", "kind", "postgres")
		} else {
			st = store.NewMemory()
			log.Warn("store", "kind", "memory", "note", "non-durable; set UTAG_DATABASE_URL for postgres")
		}
		if settings.APIToken == "" {
			log.Warn("auth", "mode", "dev", "note", "no bearer token set (UTAG_API_TOKEN)")
		}
		server := api.New(st, settings.APIToken, log)
		if settings.GithubWebhookSecret != "" {
			pemBytes, err := os.ReadFile(settings.GithubPrivateKeyFile)
			if err != nil {
				return fmt.Errorf("github private key: %w", err)
			}
			client, err := ghpkg.NewClient(settings.GithubAPIBase, settings.GithubAppID, pemBytes)
			if err != nil {
				return err
			}
			server.WebhookSecret = settings.GithubWebhookSecret
			server.GitHub = &ghpkg.Deliverer{Client: client}
			server.InstallationID = settings.GithubInstallationID
			log.Info("github", "adapter", "enabled", "api_base", settings.GithubAPIBase)
		}
		if settings.SlackSigningSecret != "" {
			server.SlackSigningSecret = settings.SlackSigningSecret
			log.Info("slack", "adapter", "enabled")
		}
		if len(settings.Routines) > 0 {
			if err := routines.Run(cmd.Context(), st, log, settings.Routines); err != nil {
				return err
			}
			log.Info("routines", "count", len(settings.Routines))
		}
		srv := &http.Server{
			Addr:              fmt.Sprintf(":%d", settings.Port),
			Handler:           server.Handler(),
			ReadHeaderTimeout: 5 * time.Second,
		}
		ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
		defer stop()
		go func() {
			<-ctx.Done() // twelve-factor IX: graceful disposability
			shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			_ = srv.Shutdown(shutdownCtx)
		}()
		log.Info("serving", "port", settings.Port)
		if err := srv.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
			return err
		}
		return nil
	},
}

func init() { rootCmd.AddCommand(serveCmd) }
