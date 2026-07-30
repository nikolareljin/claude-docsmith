from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import resources
from pathlib import Path

from . import __version__, audiences
from . import manifest as manifest_module
from .models import GenerationResult, RepoSnapshot
from .prompting import SkillRoot, build_prompt
from .providers import ProviderError, discover_model, generate_text
from .redaction import format_findings, redact
from .scanner import scan_repository

EXIT_DRIFT = 1
EXIT_SECRET_FOUND = 2


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    target_repo = Path(args.target_repo).resolve()
    if not target_repo.exists():
        parser.error(f"Target repository does not exist: {target_repo}")

    if args.check:
        return _run_check(target_repo, args.docs_dir)

    snapshot = scan_repository(
        target_repo,
        max_files=args.max_files,
        max_bytes_per_file=args.max_bytes_per_file,
        max_context_bytes=args.max_context_kb * 1024,
        skip_tests=args.skip_tests,
        redact_secrets=args.redact,
    )

    _report_redactions(snapshot)
    if args.fail_on_secret and snapshot.redactions:
        print("\nSecret-shaped content found (values withheld):", file=sys.stderr)
        print(format_findings(snapshot.redactions), file=sys.stderr)
        return EXIT_SECRET_FOUND

    selected = audiences.resolve(args.audience)
    skill_root = _resolve_skill_root()

    if args.dry_run:
        for audience in selected:
            prompt = build_prompt(
                snapshot,
                skill_root,
                audience,
                docs_dir=args.docs_dir,
                skip_checklists=args.skip_checklists,
            )
            print(f"=== AUDIENCE: {audience.key} ===")
            print(prompt)
            _print_context_stats(snapshot, prompt)
            print()
        return 0

    if args.input_json:
        try:
            result = GenerationResult.from_json_text(Path(args.input_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Failed to read input JSON: {exc}", file=sys.stderr)
            return 1
        _print_result(result)
        if args.apply:
            _apply_result(target_repo, result, args, snapshot)
        return 0

    if not args.provider:
        print(
            "No provider selected. Use --dry-run for Claude Code, --provider claude, or --provider ollama.",
            file=sys.stderr,
        )
        return 1

    try:
        model = _resolve_model(args.provider, args.model)
    except ProviderError as exc:
        print(f"Could not determine a model: {exc}", file=sys.stderr)
        return 1
    if not args.model:
        print(f"Using {args.provider} model: {model}", file=sys.stderr)

    merged = GenerationResult(summary="")
    summaries: list[str] = []
    for audience in selected:
        prompt = build_prompt(
            snapshot,
            skill_root,
            audience,
            docs_dir=args.docs_dir,
            skip_checklists=args.skip_checklists,
        )
        try:
            response_text = generate_text(args.provider, model, prompt, timeout=args.timeout)
            result = GenerationResult.from_json_text(response_text, default_audience=audience.key)
        except (ProviderError, json.JSONDecodeError) as exc:
            print(f"Generation failed for the {audience.key} track: {exc}", file=sys.stderr)
            return 1
        summaries.append(f"[{audience.key}] {result.summary}".rstrip())
        merged.files.extend(result.files)
        merged.open_questions.extend(result.open_questions)
        merged.follow_up_docs.extend(result.follow_up_docs)
    merged.summary = "\n".join(summaries)

    if args.output_json:
        Path(args.output_json).write_text(_result_to_json(merged), encoding="utf-8")

    _print_result(merged)

    if args.apply:
        _apply_result(target_repo, merged, args, snapshot)

    return 0


def _resolve_model(provider: str, explicit: str | None) -> str:
    """Resolve the model without pinning one in source.

    Precedence: ``--model`` > ``DOCSMITH_<PROVIDER>_MODEL`` > ``DOCSMITH_MODEL`` >
    whatever the provider reports it has. A hardcoded default would go stale on
    every model release, and for Ollama it would name a model the user may never
    have pulled.
    """
    if explicit:
        return explicit
    for variable in (f"DOCSMITH_{provider.upper()}_MODEL", "DOCSMITH_MODEL"):
        value = os.environ.get(variable, "").strip()
        if value:
            return value
    return discover_model(provider)


def _resolve_skill_root() -> SkillRoot:
    # One segment per call: Traversable.joinpath only accepts multiple segments
    # from Python 3.11, and this package supports 3.10.
    return resources.files("claude_docsmith").joinpath("resources").joinpath("update-docs")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Claude-ready documentation prompts and optionally run generation via Claude API or Ollama.",
    )
    parser.add_argument("target_repo", help="Path to the repository to document.")
    parser.add_argument("--version", action="version", version=f"claude-docsmith {__version__}")
    parser.add_argument("--provider", choices=["ollama", "claude"])
    parser.add_argument(
        "--model",
        required=False,
        default=None,
        help=(
            "Model name. Falls back to DOCSMITH_<PROVIDER>_MODEL, then DOCSMITH_MODEL, "
            "then whatever the provider reports it has available."
        ),
    )
    parser.add_argument(
        "--audience",
        choices=list(audiences.CHOICES),
        default="both",
        help="Which documentation track to generate (default: both, one provider call each).",
    )
    parser.add_argument("--docs-dir", default="docs", help="Documentation root inside the target repo (default: docs).")
    parser.add_argument("--dry-run", action="store_true", help="Print the assembled prompts instead of calling a model.")
    parser.add_argument("--apply", action="store_true", help="Write generated documentation files into the target repository.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Offline freshness check: compare the docs manifest against the current sources and exit 1 on drift.",
    )
    parser.add_argument("--output-json", help="Write the structured model output to a JSON file.")
    parser.add_argument("--input-json", help="Read a previously generated JSON result and optionally apply it.")
    parser.add_argument("--max-files", type=int, default=40)
    parser.add_argument("--max-bytes-per-file", type=int, default=8000)
    parser.add_argument("--max-context-kb", type=int, default=128, help="Total context byte budget in KB (default: 128).")
    parser.add_argument("--skip-tests", action="store_true", help="Exclude test files from the context.")
    parser.add_argument("--skip-checklists", action="store_true", help="Omit doc checklists from the prompt to save tokens.")
    parser.add_argument(
        "--no-redact",
        dest="redact",
        action="store_false",
        help="Disable credential redaction. Sensitive files stay excluded regardless.",
    )
    parser.set_defaults(redact=True)
    parser.add_argument(
        "--fail-on-secret",
        action="store_true",
        help="Exit 2 when credential-shaped content is found. Values are never printed.",
    )
    parser.add_argument("--timeout", type=int, default=300)
    return parser


def _run_check(target_repo: Path, docs_dir: str) -> int:
    """Offline drift gate. Never contacts a provider."""
    stored = manifest_module.read(target_repo, docs_dir)
    if stored is None:
        print(
            f"No usable manifest at {manifest_module.manifest_path(target_repo, docs_dir)}. "
            "Generate documentation first.",
            file=sys.stderr,
        )
        return EXIT_DRIFT

    snapshot = scan_repository(
        target_repo,
        max_files=stored.scan.max_files,
        max_bytes_per_file=stored.scan.max_bytes_per_file,
        max_context_bytes=stored.scan.max_context_kb * 1024,
        skip_tests=stored.scan.skip_tests,
        redact_secrets=stored.scan.redact_secrets,
    )
    current = manifest_module.source_hashes(snapshot, stored.docs_dir)
    report = manifest_module.check_drift(target_repo, stored, current)

    if report.has_drift:
        print(f"Documentation is stale (generated {stored.generated_at}):")
        print(report.render())
        return EXIT_DRIFT

    print(f"Documentation is current (generated {stored.generated_at}).")
    if report.modified_docs:
        print(report.render())
    return 0


def _apply_result(
    target_repo: Path,
    result: GenerationResult,
    args: argparse.Namespace,
    snapshot: RepoSnapshot,
) -> None:
    target_repo = target_repo.resolve()
    written: list[str] = []
    for item in result.files:
        audience = audiences.by_key(item.audience)
        if audience is None:
            raise ValueError(f"Refusing to write file with unknown audience {item.audience!r}: {item.path}")
        if not audiences.is_allowed_path(audience, item.path, args.docs_dir):
            raise ValueError(
                f"Refusing to write outside the {audience.key} track "
                f"({audiences.track_root(audience, args.docs_dir)}): {item.path}"
            )
        destination = (target_repo / item.path).resolve()
        if not destination.is_relative_to(target_repo):
            raise ValueError(f"Refusing to write outside target repository: {item.path}")

        content = item.content
        if args.redact:
            content, findings = redact(content, path=item.path)
            if findings:
                print(
                    f"Redacted {len(findings)} credential-shaped value(s) from generated {item.path}.",
                    file=sys.stderr,
                )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(item.path)

    scan = manifest_module.ScanSettings(
        max_files=args.max_files,
        max_bytes_per_file=args.max_bytes_per_file,
        max_context_kb=args.max_context_kb,
        skip_tests=args.skip_tests,
        redact_secrets=args.redact,
    )
    doc_manifest = manifest_module.build(
        snapshot=snapshot,
        result=result,
        tool_version=__version__,
        docs_dir=args.docs_dir,
        scan=scan,
    )
    path = manifest_module.write(target_repo, doc_manifest)
    print(f"\nWrote {len(written)} file(s) and updated {path.relative_to(target_repo)}.")


def _result_to_json(result: GenerationResult) -> str:
    payload = {
        "summary": result.summary,
        "files": [
            {
                "path": item.path,
                "audience": item.audience,
                "action": item.action,
                "content": item.content,
            }
            for item in result.files
        ],
        "open_questions": result.open_questions,
        "follow_up_docs": result.follow_up_docs,
    }
    return json.dumps(payload, indent=2)


def _print_result(result: GenerationResult) -> None:
    print(result.summary)
    if result.open_questions:
        print("\nOpen questions:")
        for question in result.open_questions:
            print(f"- {question}")
    print("\nPlanned files:")
    for item in result.files:
        print(f"- {item.path} ({item.audience}, {item.action})")


def _report_redactions(snapshot: RepoSnapshot) -> None:
    if snapshot.skipped_sensitive:
        print(
            f"Skipped {len(snapshot.skipped_sensitive)} sensitive file(s): "
            + ", ".join(snapshot.skipped_sensitive[:10]),
            file=sys.stderr,
        )
    if snapshot.redactions:
        kinds = ", ".join(sorted({finding.kind for finding in snapshot.redactions}))
        print(
            f"Redacted {len(snapshot.redactions)} credential-shaped value(s) before prompting ({kinds}).",
            file=sys.stderr,
        )


def _print_context_stats(snapshot: RepoSnapshot, prompt: str) -> None:
    kb = snapshot.total_bytes / 1024
    lang = snapshot.detected_language
    files = len(snapshot.scanned_files)
    prompt_bytes = len(prompt.encode("utf-8"))
    approx_tokens = prompt_bytes // 4
    print("\n--- context stats ---")
    print(f"files: {files}  content: {kb:.1f} KB  prompt: {prompt_bytes / 1024:.1f} KB  ~tokens: {approx_tokens:,}")
    print(f"detected language: {lang}")


if __name__ == "__main__":
    raise SystemExit(main())
