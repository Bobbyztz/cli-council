#!/usr/bin/env python3
"""PostToolUse hook for council skill.

Validates that run_council.py produced non-empty output.

Exit codes:
  0 — pass
  1 — non-blocking warning (stderr shown as notice)
"""
import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    stdout = data.get("tool_output", {}).get("stdout", "")

    if not command:
        sys.exit(0)

    if "run_council.py" in command:
        if not stdout or not stdout.strip():
            print("Warning: council returned empty output", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
