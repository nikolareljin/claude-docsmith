from claude_docsmith.models import GenerationResult


def test_generation_result_parses_json_code_block() -> None:
    text = """```json
    {
      "summary": "Updated docs",
      "files": [
        {
          "path": "README.md",
          "audience": "user",
          "action": "update",
          "content": "# Hello"
        }
      ],
      "open_questions": ["None"],
      "follow_up_docs": ["docs/architecture.md"]
    }
    ```"""
    result = GenerationResult.from_json_text(text)
    assert result.summary == "Updated docs"
    assert result.files[0].path == "README.md"
    assert result.follow_up_docs == ["docs/architecture.md"]
