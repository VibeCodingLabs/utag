package github

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"strings"
	"testing"
	"time"
)

func TestVerifySignature(t *testing.T) {
	body, secret := []byte(`{"a":1}`), "s3cret"
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	good := "sha256=" + hex.EncodeToString(mac.Sum(nil))
	if !VerifySignature(secret, good, body) {
		t.Fatal("valid signature rejected")
	}
	if VerifySignature(secret, "sha256=deadbeef", body) {
		t.Fatal("bad signature accepted")
	}
	if VerifySignature("", good, body) {
		t.Fatal("empty secret must never verify")
	}
}

func TestParseCommand(t *testing.T) {
	c, ok := ParseCommand("please\n/utag generate pydantic-models prompts/x.prompt.yaml\nthanks")
	if !ok || c.Target != "pydantic-models" || c.Path != "prompts/x.prompt.yaml" {
		t.Fatalf("parse failed: %+v %v", c, ok)
	}
	if _, ok := ParseCommand("/utag generate onlyonearg"); ok {
		t.Fatal("incomplete command accepted")
	}
}

func TestAppJWTShape(t *testing.T) {
	key, _ := rsa.GenerateKey(rand.Reader, 2048)
	pemKey := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(key)})
	c, err := NewClient("http://x", "12345", pemKey)
	if err != nil {
		t.Fatal(err)
	}
	tok, err := c.AppJWT(time.Unix(1_700_000_000, 0))
	if err != nil {
		t.Fatal(err)
	}
	parts := strings.Split(tok, ".")
	if len(parts) != 3 {
		t.Fatalf("jwt parts = %d", len(parts))
	}
	payload, _ := base64.RawURLEncoding.DecodeString(parts[1])
	var p struct {
		Iss string `json:"iss"`
		Iat int64  `json:"iat"`
		Exp int64  `json:"exp"`
	}
	if err := json.Unmarshal(payload, &p); err != nil {
		t.Fatal(err)
	}
	if p.Iss != "12345" || p.Exp-p.Iat != 600 {
		t.Fatalf("claims wrong: %+v", p)
	}
	// verify signature with the public key (proves RS256 correctness)
	h := sha256.Sum256([]byte(parts[0] + "." + parts[1]))
	sig, _ := base64.RawURLEncoding.DecodeString(parts[2])
	if err := rsa.VerifyPKCS1v15(&key.PublicKey, 5 /*crypto.SHA256*/, h[:], sig); err != nil {
		t.Fatalf("RS256 signature invalid: %v", err)
	}
}
