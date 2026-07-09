// Package slack: slash-command adapter. Verification per Slack's v0 signing:
// HMAC-SHA256(signing_secret, "v0:" + timestamp + ":" + raw_body), with a
// 5-minute replay window.
package slack

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strconv"
	"strings"
	"time"
)

func VerifySignature(secret, timestamp, signature string, body []byte, now time.Time) bool {
	if secret == "" || !strings.HasPrefix(signature, "v0=") {
		return false
	}
	ts, err := strconv.ParseInt(timestamp, 10, 64)
	if err != nil || now.Unix()-ts > 300 || ts-now.Unix() > 300 { // replay guard
		return false
	}
	mac := hmac.New(sha256.New, []byte(secret))
	fmt.Fprintf(mac, "v0:%s:%s", timestamp, body)
	want := "v0=" + hex.EncodeToString(mac.Sum(nil))
	return hmac.Equal([]byte(want), []byte(signature))
}

type Command struct {
	Action string // generate | status
	Target string // generate
	Repo   string // generate
	Path   string // generate
	JobID  string // status
}

// Parse: "generate <target> <owner/repo> <path>" | "status <job-id>".
func Parse(text string) (Command, string) {
	f := strings.Fields(text)
	switch {
	case len(f) == 4 && f[0] == "generate":
		return Command{Action: "generate", Target: f[1], Repo: f[2], Path: f[3]}, ""
	case len(f) == 2 && f[0] == "status":
		return Command{Action: "status", JobID: f[1]}, ""
	default:
		return Command{}, "usage: /utag generate <target> <owner/repo> <path> | /utag status <job-id>"
	}
}
