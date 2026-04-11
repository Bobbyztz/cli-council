#!/usr/bin/env python3
"""PreToolUse hook for council skill.

Blocks shell injection patterns in Bash commands.
Note: CLI invocations (codex, gemini, etc.) happen inside run_council.py
via subprocess.run with list args (no shell), so shell injection there
is not possible. This hook guards the outer bash layer only.

Exit codes:
  0 — allow
  2 — block (stderr shown to Claude and user)
"""
import json
import re
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    # Strip known safe suffixes before checking
    stripped = re.sub(r'\s*<\s*/dev/null\s*', ' ', command)
    stripped = re.sub(r'\s*2>\s*/dev/null\s*', ' ', stripped)

    # Whitelist $(pwd) — expected in council commands — then check
    # for remaining command substitutions
    stripped_for_subst = re.sub(r'\$\(pwd\)', '', stripped)

    dangerous = [
        r';\s*(rm|mv|cp|chmod|chown|curl|wget|nc|bash|sh|python3?|node|eval)\b',
        r'(?<!\|)\|(?!\|)\s*\w+',  # pipe to command (not || logical OR)
        r'>\s*/(?!dev/null)',       # redirect to file (not /dev/null)
    ]

    # Command substitution checks (on stripped_for_subst, $(pwd) removed)
    subst_patterns = [
        r'\$\([^)]*\)',  # $(...)
        r'`[^`]+`',      # backtick substitution
    ]

    for pattern in dangerous:
        if re.search(pattern, stripped):
            print(
                f"Blocked: potential shell injection. Pattern: {pattern}",
                file=sys.stderr,
            )
            sys.exit(2)

    for pattern in subst_patterns:
        if re.search(pattern, stripped_for_subst):
            print(
                f"Blocked: command substitution detected. Pattern: {pattern}",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
