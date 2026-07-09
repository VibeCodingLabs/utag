package slack

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"testing"
	"time"
)

func sig(secret, ts string, body []byte) string {
	mac := hmac.New(sha256.New, []byte(secret))
	fmt.Fprintf(mac, "v0:%s:%s", ts, body)
	return "v0=" + hex.EncodeToString(mac.Sum(nil))
}

func TestVerifySignature(t *testing.T) {
	now := time.Unix(1_700_000_000, 0)
	body, secret := []byte("token=x&text=status+abc"), "sh"
	ts := fmt.Sprint(now.Unix())
	if !VerifySignature(secret, ts, sig(secret, ts, body), body, now) {
		t.Fatal("valid rejected")
	}
	if VerifySignature(secret, ts, sig("wrong", ts, body), body, now) {
		t.Fatal("bad secret accepted")
	}
	old := fmt.Sprint(now.Add(-10 * time.Minute).Unix())
	if VerifySignature(secret, old, sig(secret, old, body), body, now) {
		t.Fatal("replay accepted")
	}
}

func TestParse(t *testing.T) {
	c, e := Parse("generate zod-schemas acme/devops prompts/x.yaml")
	if e != "" || c.Repo != "acme/devops" || c.Target != "zod-schemas" {
		t.Fatalf("%+v %q", c, e)
	}
	if c, e := Parse("status 123"); e != "" || c.JobID != "123" {
		t.Fatalf("%+v %q", c, e)
	}
	if _, e := Parse("generate onlyone"); e == "" {
		t.Fatal("bad usage accepted")
	}
}
