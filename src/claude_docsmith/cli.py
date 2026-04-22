from __future__ import annotations

import argparse
from importlib import resources
import json
from pathlib import Path
import sys

from .models import GenerationResult, RepoSnapshot
from .prompting import SkillRoot, build_prompt
from .providers import ProviderError, generate_text
from .scanner import scan_repository


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    target_repo = Path(args.target_repo).resolve()
    if not target_repo.exists():
        parser.error(f"Target repository does not exist: {target_repo}")

    snapshot = scan_repository(
        target_repo,
        max_files=args.max_files,
        max_bytes_per_file=args.max_bytes_per_file,
        max_context_bytes=args.max_context_kb * 1024,
        skip_tests=args.skip_tests,
    )

    skill_root = _resolve_skill_root()
    prompt = build_prompt(snapshot, skill_root, skip_checklists=args.skip_checklists)

    if args.dry_run:
        print(prompt)
        _print_context_stats(snapshot, prompt)
        return 0

    if args.input_json:
        try:
            result = GenerationResult.from_json_text(Path(args.input_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Failed to read input JSON: {exc}", file=sys.stderr)
            return 1
        _print_result(result)
        if args.apply:
            _apply_result(target_repo, result)
        return 0

    if not args.provider:
        print(
            "No provider selected. Use --dry-run for Claude Code, --provider claude, or --provider ollama.",
            file=sys.stderr,
        )
        return 1

    _PROVIDER_DEFAULT_MODELS = {
        "ollama": "llama3.1",
        "claude": "claude-opus-4-6",
    }
    model = args.model or _PROVIDER_DEFAULT_MODELS.get(args.provider, "")

    try:
        response_text = generate_text(args.provider, model, prompt, timeout=args.timeout)
        result = GenerationResult.from_json_text(response_text)
    except (ProviderError, json.JSONDecodeError) as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.write_text(_result_to_json(result), encoding="utf-8")

    _print_result(result)

    if args.apply:
        _apply_result(target_repo, result)

    return 0


def _resolve_skill_root() -> SkillRoot:
    return resources.files("claude_docsmith").joinpath("resources", "update-docs")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Claude-ready documentation prompts and optionally run generation via Claude API or Ollama.",
    )
    parser.add_argument("target_repo", help="Path to the repository to document.")
    parser.add_argument("--provider", choices=["ollama", "claude"])
    parser.add_argument("--model", required=False, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print the assembled prompt instead of calling a model.")
    parser.add_argument("--apply", action="store_true", help="Write generated documentation files into the target repository.")
    parser.add_argument("--output-json", help="Write the structured model output to a JSON file.")
    parser.add_argument("--input-json", help="Read a previously generated JSON result and optionally apply it.")
    parser.add_argument("--max-files", type=int, default=40)
    parser.add_argument("--max-bytes-per-file", type=int, default=8000)
    parser.add_argument("--max-context-kb", type=int, default=128, help="Total context byte budget in KB (default: 128).")
    parser.add_argument("--skip-tests", action="store_true", help="Exclude test files from the context.")
    parser.add_argument("--skip-checklists", action="store_true", help="Omit doc checklists from the prompt to save tokens.")
    parser.add_argument("--timeout", type=int, default=180)
    return parser


def _apply_result(target_repo: Path, result: GenerationResult) -> None:
    target_repo = target_repo.resolve()
    for item in result.files:
        destination = (target_repo / item.path).resolve()
        if not destination.is_relative_to(target_repo):
            raise ValueError(f"Refusing to write outside target repository: {item.path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(item.content.rstrip() + "\n", encoding="utf-8")


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
