package github

import (
	"bytes"
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client: minimal GitHub REST client. APIBase overridable (tests, GHE).
type Client struct {
	APIBase string
	AppID   string
	Key     *rsa.PrivateKey
	HTTP    *http.Client
}

func NewClient(apiBase, appID string, pemKey []byte) (*Client, error) {
	block, _ := pem.Decode(pemKey)
	if block == nil {
		return nil, errors.New("github: invalid PEM private key")
	}
	var key *rsa.PrivateKey
	if k, err := x509.ParsePKCS1PrivateKey(block.Bytes); err == nil {
		key = k
	} else if k8, err := x509.ParsePKCS8PrivateKey(block.Bytes); err == nil {
		var ok bool
		if key, ok = k8.(*rsa.PrivateKey); !ok {
			return nil, errors.New("github: PKCS8 key is not RSA")
		}
	} else {
		return nil, errors.New("github: unparseable private key")
	}
	return &Client{APIBase: apiBase, AppID: appID, Key: key,
		HTTP: &http.Client{Timeout: 30 * time.Second}}, nil
}

func b64url(b []byte) string { return base64.RawURLEncoding.EncodeToString(b) }

// AppJWT: RS256 App JWT (iss=appID, 9min expiry) — stdlib only, no jwt dep.
func (c *Client) AppJWT(now time.Time) (string, error) {
	header := b64url([]byte(`{"alg":"RS256","typ":"JWT"}`))
	payload := b64url([]byte(fmt.Sprintf(`{"iat":%d,"exp":%d,"iss":%q}`,
		now.Add(-60*time.Second).Unix(), now.Add(9*time.Minute).Unix(), c.AppID)))
	signing := header + "." + payload
	h := sha256.Sum256([]byte(signing))
	sig, err := rsa.SignPKCS1v15(rand.Reader, c.Key, crypto.SHA256, h[:])
	if err != nil {
		return "", err
	}
	return signing + "." + b64url(sig), nil
}

func (c *Client) do(method, path, token string, body, out any) error {
	var rd io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return err
		}
		rd = bytes.NewReader(b)
	}
	req, err := http.NewRequest(method, c.APIBase+path, rd)
	if err != nil {
		return err
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Authorization", "Bearer "+token)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf("github %s %s: %d %s", method, path, resp.StatusCode, b)
	}
	if out != nil {
		return json.NewDecoder(resp.Body).Decode(out)
	}
	return nil
}

func (c *Client) InstallationToken(installationID int64) (string, error) {
	jwt, err := c.AppJWT(time.Now())
	if err != nil {
		return "", err
	}
	var out struct {
		Token string `json:"token"`
	}
	err = c.do("POST", fmt.Sprintf("/app/installations/%d/access_tokens", installationID),
		jwt, map[string]any{}, &out)
	return out.Token, err
}

func (c *Client) FetchFile(token, repo, path, ref string) (string, error) {
	var out struct {
		Content  string `json:"content"`
		Encoding string `json:"encoding"`
	}
	if err := c.do("GET", fmt.Sprintf("/repos/%s/contents/%s?ref=%s", repo, path, ref),
		token, nil, &out); err != nil {
		return "", err
	}
	if out.Encoding != "base64" {
		return out.Content, nil
	}
	b, err := base64.StdEncoding.DecodeString(out.Content)
	return string(b), err
}

type prArtifact struct{ Path, Content string }

// CreateArtifactPR: git data API — blobs -> tree -> commit -> ref -> pull request.
func (c *Client) CreateArtifactPR(token, repo, base, branch, title, body string,
	artifacts []prArtifact) (string, error) {
	var ref struct {
		Object struct {
			SHA string `json:"sha"`
		} `json:"object"`
	}
	if err := c.do("GET", fmt.Sprintf("/repos/%s/git/ref/heads/%s", repo, base),
		token, nil, &ref); err != nil {
		return "", err
	}
	var baseCommit struct {
		Tree struct {
			SHA string `json:"sha"`
		} `json:"tree"`
	}
	if err := c.do("GET", fmt.Sprintf("/repos/%s/git/commits/%s", repo, ref.Object.SHA),
		token, nil, &baseCommit); err != nil {
		return "", err
	}
	type treeEntry struct {
		Path, Mode, Type, SHA string
	}
	var entries []map[string]string
	for _, a := range artifacts {
		var blob struct {
			SHA string `json:"sha"`
		}
		if err := c.do("POST", fmt.Sprintf("/repos/%s/git/blobs", repo), token,
			map[string]string{"content": a.Content, "encoding": "utf-8"}, &blob); err != nil {
			return "", err
		}
		entries = append(entries, map[string]string{
			"path": a.Path, "mode": "100644", "type": "blob", "sha": blob.SHA})
	}
	var tree struct {
		SHA string `json:"sha"`
	}
	if err := c.do("POST", fmt.Sprintf("/repos/%s/git/trees", repo), token,
		map[string]any{"base_tree": baseCommit.Tree.SHA, "tree": entries}, &tree); err != nil {
		return "", err
	}
	var commit struct {
		SHA string `json:"sha"`
	}
	if err := c.do("POST", fmt.Sprintf("/repos/%s/git/commits", repo), token,
		map[string]any{"message": title, "tree": tree.SHA,
			"parents": []string{ref.Object.SHA}}, &commit); err != nil {
		return "", err
	}
	if err := c.do("POST", fmt.Sprintf("/repos/%s/git/refs", repo), token,
		map[string]string{"ref": "refs/heads/" + branch, "sha": commit.SHA}, nil); err != nil {
		return "", err
	}
	var pr struct {
		HTMLURL string `json:"html_url"`
	}
	if err := c.do("POST", fmt.Sprintf("/repos/%s/pulls", repo), token,
		map[string]string{"title": title, "head": branch, "base": base, "body": body},
		&pr); err != nil {
		return "", err
	}
	return pr.HTMLURL, nil
}

func (c *Client) Comment(token, repo string, issue int, body string) error {
	return c.do("POST", fmt.Sprintf("/repos/%s/issues/%d/comments", repo, issue),
		token, map[string]string{"body": body}, nil)
}
