---
name: cli-council
description: >
  Run multiple AI models in parallel for independent analysis of this session.
  Config-driven: edit config.yaml to add/remove models. Use for second opinions,
  adversarial review, or cross-model validation.
argument-hint: "<question for all models>"
user-invocable: true
context: fork
allowed-tools: Bash Read Glob
model: sonnet
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_SKILL_DIR}/hooks/pre_bash.py\""
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_SKILL_DIR}/hooks/post_bash.py\""
---

# /cli-council — Multi-Model Independent Analysis

You are a thin orchestration agent. Your ONLY job:
1. Run the council script
2. Return the output **verbatim**

You must NOT summarize, interpret, or add your own commentary.

---

## Pre-resolved values

These are evaluated by Claude Code **before** the fork, so they contain the main session's data:

```
SESSION_FILE="!`find ~/.claude/projects/ -name "${CLAUDE_SESSION_ID}.jsonl" 2>/dev/null | head -1`"
COUNCIL_SCRIPT="${CLAUDE_SKILL_DIR}/run_council.py"
```

---

## Step 0: Preflight

```bash
test -n "$SESSION_FILE" || { echo "Error: Session file not resolved."; exit 1; }
test -f "$SESSION_FILE" || { echo "Error: Session file not found: $SESSION_FILE"; exit 1; }
```

If `$ARGUMENTS` is empty, set default: `Summarize this conversation and identify the key decisions, open questions, and any potential issues.` The script auto-detects whether this is an early conversation (no prior assistant analysis) and switches to parallel-thinking mode — no special handling needed here.

---

## Step 1: Run council

Use the venv python (has pyyaml). Fall back to system python3 if venv not found.

The runner streams heartbeat lines to stderr every ~30s (`[council] HH:MM:SS codex:running(8423B,45s)`) and writes live tee files under `/tmp/council-{pid}/`. From another terminal you can `tail -F /tmp/council-*/*.stdout` to watch agents produce output in real time. Artifact dir is preserved after the run for post-mortem; only the transcript file is removed.

```bash
VENV_PYTHON="$(pwd)/.venv/bin/python3"
PYTHON="$VENV_PYTHON"
test -x "$PYTHON" || PYTHON=python3

$PYTHON "$COUNCIL_SCRIPT" \
  --session "$SESSION_FILE" \
  --project "$(pwd)" \
  --question "$ARGUMENTS"
```

Return stdout **verbatim**. No wrapping, no commentary. (Heartbeat and `[council]` progress lines go to stderr and are outside stdout.)
