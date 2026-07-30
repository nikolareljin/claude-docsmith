"""Keep credentials out of prompts, provider requests, and generated docs.

Two layers:

* :func:`is_sensitive_path` refuses whole files by name, before they are opened.
* :func:`redact` scrubs credential-shaped content out of files that are read.

Findings never carry the matched value. Only ``path``, ``line``, and ``kind``
are recorded, so a finding can be printed or written to a manifest safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import PurePosixPath
import re


@dataclass(frozen=True, slots=True)
class Finding:
    """A redacted match. Deliberately does not store the secret itself."""

    path: str
    line: int
    kind: str


MARKER_TEMPLATE = "[REDACTED:{kind}]"


# --- file-level deny list -------------------------------------------------

_SENSITIVE_NAMES = {
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".htpasswd",
    ".pgpass",
    "credentials",
}

_SENSITIVE_GLOBS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.jks",
    "*.keystore",
    "*.kubeconfig",
    "id_rsa*",
    "id_ed25519*",
    "id_ecdsa*",
    "*credentials*.json",
    "secrets.*",
    "terraform.tfstate*",
)

# Sample env files are the documented way to describe configuration, so they
# are read on purpose. Their values still go through redact().
_ENV_ALLOW = {
    ".env.example",
    ".env.sample",
    ".env.template",
    ".env.dist",
}


def is_sensitive_path(rel_path: str) -> bool:
    """Return True when a file should never be opened for documentation context."""
    name = PurePosixPath(rel_path).name
    if name in _ENV_ALLOW:
        return False
    if name in _SENSITIVE_NAMES:
        return True
    return any(fnmatch(name, glob) for glob in _SENSITIVE_GLOBS)


# --- content-level redaction ----------------------------------------------

# Ordered most specific first: the first pattern to claim a span wins.
# A pattern may define a "secret" group to redact only part of the match.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private-key-block",
        re.compile(
            r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----"
        ),
    ),
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("openai-key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{32,}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("github-pat", re.compile(r"github_pat_[A-Za-z0-9_]{40,}")),
    ("slack-token", re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("stripe-key", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"),
    ),
    (
        "url-credentials",
        re.compile(r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/@]+:)(?P<secret>[^\s:/@]+)(?=@)"),
    ),
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(?P<key>[A-Za-z0-9_.\-]*"
            r"(?:passwd|password|passphrase|secret|token|credential"
            r"|api[_\-]?key|access[_\-]?key|private[_\-]?key|auth[_\-]?token|authorization)"
            r"[A-Za-z0-9_.\-]*)\s*[:=]\s*(?P<quote>[\"']?)(?P<secret>[^\s\"',;}{]{8,})(?P=quote)"
        ),
    ),
)

_PLACEHOLDER_TOKENS = (
    "changeme",
    "change-me",
    "your-",
    "your_",
    "yourkey",
    "example",
    "dummy",
    "sample",
    "placeholder",
    "redacted",
    "todo",
    "fixme",
    "notreal",
    "fake",
    "insert",
    "replace",
    "<",
    "${",
    "$(",
    "{{",
)

_PLACEHOLDER_EXACT = {
    "null",
    "none",
    "nil",
    "true",
    "false",
    "empty",
    "unset",
    "password",
    "secret",
    "token",
}

_MASKED_RE = re.compile(r"^[x*.\-_0]+$", re.IGNORECASE)

# The generic assignment rule matches any `password = <value>` shape, including
# source that merely *references* a credential (`api_key = os.environ.get(...)`,
# `redact_secrets=args.redact`). These keep it from flagging code and prose.
_CODE_CHARS = set("()[]{}<>$,;\\!?*%&|`\"'")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_OPAQUE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-+/=.:]+$")


def _looks_like_secret_value(value: str) -> bool:
    """Heuristic for the generic assignment rule only. Vendor patterns bypass it."""
    candidate = value.strip().strip("\"'")
    if any(char in _CODE_CHARS for char in candidate) or ".." in candidate:
        return False
    if _IDENTIFIER_RE.match(candidate):  # dotted identifier, e.g. args.redact
        return False
    if not _OPAQUE_TOKEN_RE.match(candidate):
        return False
    has_digit = any(char.isdigit() for char in candidate)
    has_alpha = any(char.isalpha() for char in candidate)
    return (has_digit and has_alpha) or len(candidate) >= 20


def is_placeholder(value: str) -> bool:
    """Return True for documentation stand-ins that must not be flagged as secrets."""
    candidate = value.strip().strip("\"'")
    if len(candidate) < 8:
        return True
    lowered = candidate.lower()
    if lowered in _PLACEHOLDER_EXACT:
        return True
    if _MASKED_RE.match(candidate):
        return True
    if candidate.startswith(MARKER_TEMPLATE[:10]):
        return True
    return any(token in lowered for token in _PLACEHOLDER_TOKENS)


def redact(text: str, *, path: str) -> tuple[str, list[Finding]]:
    """Replace credential-shaped spans in ``text`` with redaction markers.

    Returns the scrubbed text and one :class:`Finding` per replacement.
    """
    spans: list[tuple[int, int, str]] = []
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            start, end = (
                match.span("secret") if "secret" in (match.groupdict() or {}) else match.span()
            )
            if start < 0 or end <= start:
                continue
            matched = text[start:end]
            if is_placeholder(matched):
                continue
            if kind == "credential-assignment" and not _looks_like_secret_value(matched):
                continue
            spans.append((start, end, kind))

    if not spans:
        return text, []

    spans.sort(key=lambda item: (item[0], -item[1]))

    findings: list[Finding] = []
    pieces: list[str] = []
    cursor = 0
    for start, end, kind in spans:
        if start < cursor:  # already covered by a more specific pattern
            continue
        pieces.append(text[cursor:start])
        pieces.append(MARKER_TEMPLATE.format(kind=kind))
        findings.append(Finding(path=path, line=text.count("\n", 0, start) + 1, kind=kind))
        cursor = end
    pieces.append(text[cursor:])

    return "".join(pieces), findings


def summarize(findings: list[Finding]) -> list[dict[str, object]]:
    """Collapse findings into ``{path, kind, count}`` records for the manifest."""
    counts: dict[tuple[str, str], int] = {}
    for finding in findings:
        key = (finding.path, finding.kind)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"path": path, "kind": kind, "count": count}
        for (path, kind), count in sorted(counts.items())
    ]


def format_findings(findings: list[Finding]) -> str:
    """Render findings as ``path:line kind`` lines. Never includes the value."""
    return "\n".join(f"{f.path}:{f.line} {f.kind}" for f in findings)
