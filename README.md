# cli-council

Get independent analysis from multiple AI models — without leaving Claude Code.

One command. Full session context. Parallel execution. No manual copy-paste.

```
> /cli-council Is this migration plan safe?

══════════════════════════════════════════════════
  Codex (GPT-5.4)  (42.3s)
══════════════════════════════════════════════════

The plan misses a critical edge case: concurrent writes
during the backfill window...

══════════════════════════════════════════════════
  Gemini 3.1 Pro  (38.7s)
══════════════════════════════════════════════════

Two concerns. First, the rollback strategy assumes...
```

## The problem

You're deep in a Claude Code session — you've discussed a design, read files, made decisions. Now you want a second opinion.

The obvious approach: open another terminal, start Codex or Gemini, and... manually re-explain everything. Copy the plan. Paste the context. Hope you didn't miss anything.

Or use a fancy multi-agent terminal (Warp, Conductor, cmux) that promises seamless context sharing between AI agents. Except when you actually try it: the TUI swallows keyboard shortcuts, the "attach as context" button doesn't exist, and you end up manually exporting a `FULL_CONTEXT.md` file anyway — which has nothing to do with the terminal tool.

**The real problem isn't the terminal. It's the data.** How do you transfer one agent's full accumulated context to another, losslessly, without manual intervention?

## The solution

cli-council reads Claude Code's native session data (the `.jsonl` file where every message, tool call, and result is stored), builds a complete transcript enriched with project context (`CLAUDE.md`, memory index), and feeds it directly to other AI CLIs in parallel.

No UI layer. No manual export. No context loss.

```
Session JSONL ──→ extract ──→ build transcript ──→ parallel CLI calls ──→ labeled output
                  (full conversation)   (+ CLAUDE.md, memory)    (codex, gemini, ...)
```

## Install

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code) + at least one other AI CLI ([Codex](https://github.com/openai/codex), [Gemini CLI](https://github.com/google-gemini/gemini-cli), etc.)

1. Clone into your Claude Code skills directory:

```bash
git clone https://github.com/Bobbyztz/cli-council.git .claude/skills/cli-council
```

2. Install the one Python dependency:

```bash
pip install pyyaml
# or, if your project uses a venv:
.venv/bin/pip install pyyaml
```

3. That's it. Claude Code auto-discovers skills in `.claude/skills/`.

## Usage

Inside any Claude Code session:

```
/cli-council <your question>
```

Examples:

```
/cli-council Does this refactoring plan have any blind spots?
/cli-council Check the security implications of this approach.
/cli-council What am I missing?
```

Without arguments, it defaults to summarizing the session and identifying key decisions, open questions, and potential issues.

### Two modes (auto-detected)

| Mode | When | What happens |
|------|------|-------------|
| **Parallel thinking** | No assistant responses yet (first message) | Each model independently analyzes the project context and answers your question |
| **Session review** | Conversation in progress | Each model reviews the full Claude Code session and gives independent feedback |

## Configuration

Edit `config.yaml` to enable/disable agents or add new ones:

```yaml
agents:
  codex:
    enabled: true
    binary: codex
    display_name: "Codex (GPT-5.4)"
    timeout: 300
    args_before:
      - exec
      - --sandbox
      - read-only
      - --full-auto
      - --skip-git-repo-check
      - -m
      - gpt-5.4
    args_after: []

  gemini:
    enabled: true
    binary: gemini
    display_name: "Gemini 3.1 Pro"
    timeout: 300
    args_before:
      - -m
      - gemini-3.1-pro-preview
    args_after:
      - --yolo
      - -o
      - text

  # Add your own:
  # qwen:
  #   enabled: true
  #   binary: qwen-cli
  #   display_name: "Qwen Max"
  #   timeout: 300
  #   args_before: [--model, qwen-max]
  #   args_after: []
```

Any CLI that accepts a text prompt as a positional argument works. If the binary isn't found on `$PATH`, that agent is silently skipped.

## How it works

**6 files, ~650 lines total.**

| File | What it does |
|------|-------------|
| `SKILL.md` | Skill definition — tells Claude Code to run the script and return output verbatim |
| `config.yaml` | Agent registry — binaries, args, timeouts |
| `run_council.py` | Core engine — builds transcript, launches agents in parallel via threads, collects output |
| `extract_session.py` | Session parser — reads Claude Code's `.jsonl` format, extracts full conversation (text + tool calls + results, excludes thinking blocks) |
| `hooks/pre_bash.py` | Security — blocks shell injection patterns in the orchestration layer |
| `hooks/post_bash.py` | Validation — warns if the council script returns empty output |

### Context assembly

The transcript sent to each agent includes:

1. **CLAUDE.md** — project instructions and conventions
2. **MEMORY.md** — persistent memory index (cross-session context)
3. **Full conversation** — every user message, assistant response, tool call, and tool result from the current session

All wrapped in XML tags with a preamble instructing the receiving model to treat the content as analysis material, not instructions to follow.

### Security

- All CLI invocations use `subprocess.run` with list args (no shell) — shell injection at the subprocess level is structurally impossible
- The `pre_bash.py` hook blocks injection patterns (pipes, command substitution, dangerous redirects) in the outer bash layer
- Each agent's prompt explicitly instructs read-only behavior: no file creation, modification, or deletion
- Temporary transcript files are cleaned up in a `finally` block

## Limitations

- **Snapshot, not stream.** cli-council captures the session state at invocation time. It doesn't support continuous context sharing or multi-phase workflows (e.g., "Codex watches while Claude implements, then reviews").
- **One-directional.** Other models analyze and respond, but can't act on the codebase.
- **CLI availability.** Each agent needs its CLI installed and authenticated. If a binary isn't on `$PATH`, that agent is skipped.
- **Token limits.** Long sessions produce large transcripts. The receiving model's context window is the bottleneck.

## License

[MIT](LICENSE)
