#!/usr/bin/env python3
"""Extract conversation from Claude Code session JSONL files.

Full-fidelity extraction — preserves text, tool calls, and tool results.
Only thinking blocks are excluded (internal reasoning).
"""
import json
import sys


def _format_tool_input(input_data: dict) -> str:
    """Format tool input as indented key-value pairs."""
    if not input_data:
        return ""
    lines = []
    for key, value in input_data.items():
        if isinstance(value, str):
            # Multi-line string values: indent continuation lines
            if "\n" in value:
                first, *rest = value.split("\n")
                lines.append(f"  {key}: {first}")
                for r in rest:
                    lines.append(f"    {r}")
            else:
                lines.append(f"  {key}: {value}")
        elif isinstance(value, (int, float, bool)):
            lines.append(f"  {key}: {value}")
        else:
            lines.append(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines)


def _format_tool_result_content(content) -> str:
    """Format tool result content (string, list of blocks, or other)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "image":
                    parts.append("[image]")
                else:
                    parts.append(json.dumps(block, ensure_ascii=False))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def extract_conversation(filepath: str) -> str:
    """Extract full conversation from a Claude Code session JSONL file."""
    entries = []
    with open(filepath) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            record_type = record.get("type")
            if record_type not in ("user", "assistant"):
                continue

            message = record.get("message", {})
            content_blocks = message.get("content", [])
            # Normalize: short user messages arrive as plain strings, not
            # block lists. Iterating a string gave chars (not dicts), so
            # every block was skipped and the turn was silently dropped.
            if isinstance(content_blocks, str):
                content_blocks = [{"type": "text", "text": content_blocks}]

            parts = []
            for block in content_blocks:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")

                if block_type == "text":
                    text = block.get("text", "").strip()
                    if text:
                        parts.append(text)

                elif block_type == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    header = f"[tool_use] {tool_name}"
                    params = _format_tool_input(tool_input)
                    parts.append(f"{header}\n{params}" if params else header)

                elif block_type == "tool_result":
                    content = block.get("content", "")
                    result_text = _format_tool_result_content(content)
                    if result_text.strip():
                        parts.append(f"[tool_result]\n{result_text}")
                    else:
                        parts.append("[tool_result] (empty)")

                # Skip: thinking, thinking_delta, redacted_thinking

            if parts:
                # User messages with only tool_result (no text) get a distinct label
                if record_type == "user":
                    has_text = any(
                        isinstance(b, dict) and b.get("type") == "text"
                        and b.get("text", "").strip()
                        for b in content_blocks
                    )
                    role = "USER" if has_text else "TOOL_RESULT"
                else:
                    role = "ASSISTANT"
                separator = f"──── {role} ────"
                entries.append(f"{separator}\n\n" + "\n\n".join(parts))

    return "\n\n".join(entries)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_session.py <session.jsonl>", file=sys.stderr)
        sys.exit(1)

    try:
        print(extract_conversation(sys.argv[1]))
    except FileNotFoundError:
        print(f"Error: File not found: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)
