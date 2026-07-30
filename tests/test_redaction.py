"""All fixture values here are deliberately fake and structurally invalid."""

import pytest

from claude_docsmith.redaction import (
    format_findings,
    is_placeholder,
    is_sensitive_path,
    redact,
    summarize,
)

FAKE = {
    "anthropic-key": "sk-ant-" + "A" * 24,
    "openai-key": "sk-" + "B" * 40,
    "github-token": "ghp_" + "C" * 36,
    "github-pat": "github_pat_" + "D" * 45,
    "slack-token": "xoxb-" + "1" * 12 + "-" + "2" * 12,
    "stripe-key": "sk_test_" + "E" * 24,
    "google-api-key": "AIza" + "F" * 35,
    "aws-access-key-id": "AKIA" + "Z" * 16,
    "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.QQQQQQQQQQQQ",
}


@pytest.mark.parametrize("kind,value", sorted(FAKE.items()))
def test_each_pattern_is_redacted(kind: str, value: str) -> None:
    text = f"credential = {value}\n"
    scrubbed, findings = redact(text, path="src/app.py")
    assert value not in scrubbed
    assert findings, f"{kind} produced no finding"


def test_private_key_block_is_redacted() -> None:
    text = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIBOgIBAAJBAK\nnotarealkey\n"
        "-----END RSA PRIVATE KEY-----\n"
    )
    scrubbed, findings = redact(text, path="deploy/key.txt")
    assert "notarealkey" not in scrubbed
    assert findings[0].kind == "private-key-block"


def test_url_credentials_keep_scheme_and_host() -> None:
    text = "postgres://appuser:hunter2hunter2@db.internal:5432/app"
    scrubbed, findings = redact(text, path="config.py")
    assert "hunter2hunter2" not in scrubbed
    assert "postgres://appuser:" in scrubbed
    assert "@db.internal:5432/app" in scrubbed
    assert findings[0].kind == "url-credentials"


def test_generic_assignment_keeps_the_key_name() -> None:
    scrubbed, findings = redact('DATABASE_PASSWORD = "s3cretValue123"', path="settings.py")
    assert "DATABASE_PASSWORD" in scrubbed
    assert "s3cretValue123" not in scrubbed
    assert findings[0].kind == "credential-assignment"


@pytest.mark.parametrize(
    "line",
    [
        "API_KEY=your-key-here",
        "PASSWORD=changeme",
        "TOKEN=<your-token>",
        "SECRET=${VAULT_SECRET}",
        "CLIENT_SECRET=xxxxxxxxxxxx",
        "API_KEY=example-value",
    ],
)
def test_placeholders_are_not_flagged(line: str) -> None:
    scrubbed, findings = redact(line, path=".env.example")
    assert scrubbed == line
    assert findings == []


def test_short_values_are_treated_as_placeholders() -> None:
    assert is_placeholder("abc")
    assert not is_placeholder("s3cretValue123")


def test_findings_never_carry_the_secret_value() -> None:
    value = FAKE["anthropic-key"]
    _, findings = redact(f"key = {value}", path="src/app.py")
    rendered = format_findings(findings)
    assert value not in rendered
    assert rendered.startswith("src/app.py:1 ")
    for finding in findings:
        assert value not in repr(finding)


def test_line_numbers_are_reported() -> None:
    text = "line one\nline two\nkey = " + FAKE["github-token"] + "\n"
    _, findings = redact(text, path="src/app.py")
    assert findings[0].line == 3


def test_summarize_groups_by_path_and_kind() -> None:
    value = FAKE["aws-access-key-id"]
    _, findings = redact(f"a = {value}\nb = {value}\n", path="src/app.py")
    assert summarize(findings) == [{"path": "src/app.py", "kind": "aws-access-key-id", "count": 2}]


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.production",
        "config/server.pem",
        "certs/private.key",
        "secrets/keystore.p12",
        "deploy/id_rsa",
        "deploy/id_ed25519.pub",
        "home/.netrc",
        "aws/credentials",
        "gcp/service-credentials.json",
        "app/secrets.yaml",
        "infra/terraform.tfstate.backup",
    ],
)
def test_sensitive_paths_are_denied(path: str) -> None:
    assert is_sensitive_path(path)


@pytest.mark.parametrize(
    "path",
    [
        ".env.example",
        ".env.sample",
        ".env.template",
        "README.md",
        "src/keychain.py",
        "docs/secrets-policy.md",
    ],
)
def test_ordinary_paths_are_allowed(path: str) -> None:
    assert not is_sensitive_path(path)


@pytest.mark.parametrize(
    "line",
    [
        'api_key = os.environ.get("ANTHROPIC_API_KEY", "")',
        "redact_secrets=args.redact,",
        'redact_secrets=scan_payload.get("redact_secrets", True),',
        "export ANTHROPIC_API_KEY=sk-ant-...",
        "password: str = field(default_factory=str)",
        "token = build_token(request)",
    ],
)
def test_code_that_references_a_credential_is_not_flagged(line: str) -> None:
    scrubbed, findings = redact(line, path="src/app.py")
    assert scrubbed == line
    assert findings == []


@pytest.mark.parametrize(
    "line",
    [
        'DATABASE_PASSWORD = "s3cretValue123"',
        "api_key=Zm9vYmFyMTIzNDU2Nzg5MA",
        "client_secret: aaaaaaaaaaaaaaaaaaaaaaaa",
    ],
)
def test_opaque_assigned_values_are_still_flagged(line: str) -> None:
    _, findings = redact(line, path="src/app.py")
    assert [f.kind for f in findings] == ["credential-assignment"]
