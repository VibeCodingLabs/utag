// Package github: GitHub App adapter — webhook verification, command parsing,
// App JWT auth, installation tokens, and PR delivery via the git data API.
package github

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"regexp"
)

// VerifySignature: X-Hub-Signature-256 = "sha256=" + hex(HMAC-SHA256(secret, body)).
func VerifySignature(secret, header string, body []byte) bool {
	if secret == "" || len(header) < 8 || header[:7] != "sha256=" {
		return false
	}
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	want := hex.EncodeToString(mac.Sum(nil))
	return hmac.Equal([]byte(want), []byte(header[7:]))
}

var cmdRe = regexp.MustCompile(`(?m)^/utag\s+generate\s+(\S+)\s+(\S+)\s*$`)

type Command struct {
	Target string
	Path   string
}

// ParseCommand extracts "/utag generate <target> <path>" from a comment body.
func ParseCommand(body string) (Command, bool) {
	m := cmdRe.FindStringSubmatch(body)
	if m == nil {
		return Command{}, false
	}
	return Command{Target: m[1], Path: m[2]}, true
}

type CommentEvent struct {
	Action  string `json:"action"`
	Comment struct {
		Body string `json:"body"`
	} `json:"comment"`
	Issue struct {
		Number int `json:"number"`
	} `json:"issue"`
	Repository struct {
		FullName      string `json:"full_name"`
		DefaultBranch string `json:"default_branch"`
	} `json:"repository"`
	Installation struct {
		ID int64 `json:"id"`
	} `json:"installation"`
}

func ParseCommentEvent(body []byte) (*CommentEvent, error) {
	var e CommentEvent
	return &e, json.Unmarshal(body, &e)
}

// JobMeta rides on the job (Job.Metadata) so delivery knows where the PR goes.
type JobMeta struct {
	Repo           string `json:"repo"`
	InstallationID int64  `json:"installation_id"`
	BaseBranch     string `json:"base_branch"`
	IssueNumber    int    `json:"issue_number"`
	SourcePath     string `json:"source_path"`
}
