package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// Settings: ONE struct, filled automatically by viper (dogfoods the pattern
// utag's go-harness generator emits). Precedence: flag > env UTAG_* > file > default.
type Settings struct {
	Port        int    `mapstructure:"port" json:"port"`
	LogLevel    string `mapstructure:"log-level" json:"log-level"`
	DatabaseURL string `mapstructure:"database-url" json:"database-url"`
	APIToken    string `mapstructure:"api-token" json:"-"` // never serialized (secret)
	// GitHub App adapter (all optional; adapter off unless webhook secret set)
	GithubWebhookSecret  string `mapstructure:"github-webhook-secret" json:"-"`
	GithubAppID          string `mapstructure:"github-app-id" json:"github-app-id"`
	GithubPrivateKeyFile string `mapstructure:"github-private-key-file" json:"github-private-key-file"`
	GithubAPIBase        string `mapstructure:"github-api-base" json:"github-api-base"`
}

var (
	v        = viper.New()
	settings Settings
	cfgFile  string
)

var rootCmd = &cobra.Command{
	Use:   "utag-control-plane",
	Short: "utag control-plane: job API hub for the agent harness",
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func init() {
	cobra.OnInitialize(initConfig)
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default ./utag.yaml)")
	rootCmd.PersistentFlags().Int("port", 8080, "listen port")
	rootCmd.PersistentFlags().String("log-level", "info", "log level")
	rootCmd.PersistentFlags().String("database-url", "", "postgres URL; empty = in-memory store")
	rootCmd.PersistentFlags().String("api-token", "", "bearer token; empty = dev mode")
	rootCmd.PersistentFlags().String("github-webhook-secret", "", "GitHub App webhook secret")
	rootCmd.PersistentFlags().String("github-app-id", "", "GitHub App ID")
	rootCmd.PersistentFlags().String("github-private-key-file", "", "GitHub App private key PEM path")
	rootCmd.PersistentFlags().String("github-api-base", "https://api.github.com", "GitHub API base URL")
	_ = v.BindPFlags(rootCmd.PersistentFlags())
}

func initConfig() {
	v.SetDefault("port", 8080)
	v.SetDefault("log-level", "info")
	v.SetDefault("github-api-base", "https://api.github.com")
	if cfgFile != "" {
		v.SetConfigFile(cfgFile)
	} else {
		v.SetConfigName("utag")
		v.SetConfigType("yaml")
		v.AddConfigPath(".")
	}
	v.SetEnvPrefix("UTAG")
	v.SetEnvKeyReplacer(strings.NewReplacer("-", "_", ".", "_"))
	v.AutomaticEnv()
	_ = v.ReadInConfig()
	if err := v.Unmarshal(&settings); err != nil {
		fmt.Fprintln(os.Stderr, "config:", err)
		os.Exit(1)
	}
}
