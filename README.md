# cli-council

Get independent analysis from multiple AI models — without leaving Claude Code.

One command. Full session context. Parallel execution with live progress. No manual copy-paste.

```
> /cli-council Is this migration plan safe?

[council] main_pid=48291
[council] agents=['codex', 'gemini']
[council] artifact dir: /tmp/council-48291
[council] 14:32:08 codex:running(out=0B,err=12KB,31s)  gemini:running(out=0B,err=0B,31s)

══════════════════════════════════════════════════
  Codex (GPT-5.5)  (42.3s)  state=completed
══════════════════════════════════════════════════

The plan misses a critical edge case: concurrent writes
during the backfill window...

══════════════════════════════════════════════════
  Gemini 2.5 Pro  (58.7s)  state=completed
══════════════════════════════════════════════════

QUOTE:
> The migration runs ALTER TABLE ADD COLUMN with a DEFAULT
> backfill. The rollback plan says "drop the column" but
> doesn't address rows written during the backfill window
> with the new schema...

PARAPHRASE: Participants assume rollback is clean because
the column can be dropped.

PROBLEM: Rows inserted during backfill may reference the
new column in application logic; DROP COLUMN doesn't undo
those writes.

SEVERITY: HIGH

──────────────────────────────────────────────────
[council] AUDIT_FULL — 2/2 completed.
```

## The problem

You're deep in a Claude Code session — you've discussed a design, read files, made decisions. Now you want a second opinion.

The obvious approach: open another terminal, start Codex or Gemini, and... manually re-explain everything. Copy the plan. Paste the context. Hope you didn't miss anything.

Or use a fancy multi-agent terminal that promises seamless context sharing between AI agents. Except when you actually try it: the TUI swallows keyboard shortcuts, the "attach as context" button doesn't exist, and you end up manually exporting a `FULL_CONTEXT.md` file anyway.

**The real problem isn't the terminal. It's the data.** How do you transfer one agent's full accumulated context to another, losslessly, without manual intervention?

## The solution

cli-council reads Claude Code's native session data (the `.jsonl` file where every message, tool call, and result is stored), builds a complete transcript enriched with project context (`CLAUDE.md`, memory index), and feeds it directly to other AI CLIs in parallel — with streaming progress, automatic error handling, and machine-readable audit status.

```
Session JSONL ──→ extract ──→ build transcript ──→ parallel CLI calls ──→ labeled output
                  (full conversation)   (+ CLAUDE.md, memory)    (codex, gemini, ...)
                                                                         │
                                                              /tmp/council-{pid}/
                                                              ├── codex.stdout  (live tee)
                                                              ├── codex.stderr
                                                              ├── codex.meta    (JSON state)
                                                              ├── gemini.stdout
                                                              ├── gemini.stderr
                                                              ├── gemini.meta
                                                              └── heartbeat.log
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

### Live monitoring

While agents are running, a heartbeat prints to stderr every 30 seconds:

```
[council] 14:32:08 codex:running(out=0B,err=12KB,31s)  gemini:running(out=0B,err=0B,31s)
[council] 14:32:38 codex:running(out=8KB,err=24KB,61s)  gemini:running(out=3KB,err=0B,61s)
```

From another terminal, watch agents produce output in real time:

```bash
tail -F /tmp/council-*/*.stdout
```

Results stream as each agent completes (fastest first), so you don't wait for the slowest agent before seeing anything.

## Configuration

Edit `config.yaml` to enable/disable agents, tune error handling, or add new CLIs.

### Agents

```yaml
agents:
  codex:
    enabled: true
    binary: codex
    display_name: "Codex (GPT-5.5)"
    timeout: 750
    args_before:
      - exec
      - --sandbox
      - read-only
      - --full-auto
      - --skip-git-repo-check
      - -m
      - gpt-5.5
    args_after: []

  gemini:
    enabled: true
    binary: gemini
    display_name: "Gemini 2.5 Pro"
    timeout: 600
    transcript_mode: file   # agent reads transcript from disk (no ARG_MAX limit)
    prompt_prefix: |        # anti-sycophancy framing (see below)
      The user reviewing this session believes there ARE problems...
    args_before:
      - -m
      - gemini-2.5-pro
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

### Per-agent options

| Option | Default | What it does |
|--------|---------|-------------|
| `transcript_mode` | `"inline"` | `"inline"`: embed transcript in prompt (subject to ARG_MAX ~1MB). `"file"`: write transcript to disk, agent reads it via tool call (no size limit). |
| `prompt_prefix` | `""` | Text prepended to the agent's prompt. Use for model-specific framing (e.g., anti-sycophancy instructions for Gemini). |
| `timeout` | `300` | Max seconds before the agent is terminated. |

### Error handling

Errors are classified by regex patterns in `config.yaml`, then handled per-category:

```yaml
error_policy:
  network:
    retry: 3
    backoff_s: [2, 5, 15]
  quota:
    retry: 0    # skip immediately — agent unavailable this round
  other:
    retry: 0

error_patterns:
  quota:
    - "rate.?limit"
    - "\\b429\\b"
    - "too many requests"
  network:
    - "connection refused"
    - "dns.*(fail|error|lookup)"
    - "\\b50[234]\\b"
```

- **Network errors**: retry with exponential backoff (configurable). Prior attempt artifacts are preserved as `agent.attempt1.stderr` etc.
- **Quota / rate limit**: skip the agent immediately. The other agent still runs. No wasted retries.
- **Other errors**: preserved as-is for debugging.

To change classification, edit the regex patterns — no code changes needed.

### Audit status

The final output line is machine-readable:

| Status | Meaning |
|--------|---------|
| `AUDIT_FULL` | All agents completed |
| `AUDIT_PARTIAL_QUOTA` | Some agents quota-skipped, rest completed. Audit still valid. |
| `AUDIT_BLOCKED` | Real failure — 0 agents completed, or non-quota failure. Cannot substitute self-review. |

## How it works

**6 files, ~1100 lines total.**

| File | What it does |
|------|-------------|
| `SKILL.md` | Skill definition — tells Claude Code to run the script and return output verbatim |
| `config.yaml` | Agent registry, error policy, error patterns, heartbeat interval |
| `run_council.py` | Core engine — transcript building, `AgentProc` state machine, streaming IO, heartbeat, retry logic, signal handling, audit status |
| `extract_session.py` | Session parser — reads Claude Code's `.jsonl` format, extracts full conversation (text + tool calls + results, excludes thinking blocks) |
| `hooks/pre_bash.py` | Security — blocks shell injection patterns in the orchestration layer |
| `hooks/post_bash.py` | Validation — warns if the council script returns empty output |

### Context assembly

The transcript sent to each agent includes:

1. **CLAUDE.md** — project instructions and conventions
2. **MEMORY.md** — persistent memory index (cross-session context)
3. **Full conversation** — every user message, assistant response, tool call, and tool result from the current session

All wrapped in XML tags with a preamble instructing the receiving model to treat the content as analysis material, not instructions to follow.

### Primary-source grounding

A protocol injected into every review prompt that forces agents to read the actual files referenced in the session — not just the transcript's paraphrases. This catches misquotes, cherry-picked excerpts, and paraphrase drift that transcript-only review inherits silently.

### Anti-sycophancy (Gemini)

Gemini's `prompt_prefix` in `config.yaml` reframes the review task: *"this work is flawed in ways the participants did not catch."* Instead of fighting agreement bias, it channels it — the model agrees with the premise that problems exist, and looks harder. Each concern must include a multi-line quote with surrounding context, a paraphrase (committing to an interpretation), and severity tied to decision impact.

### Process management

Each agent is an `AgentProc` with a state machine:

```
pending → starting → running → completed
                             → timeout    (SIGTERM → SIGKILL escalation)
                             → error      (classified → retry or give up)
                             → skipped    (quota — agent unavailable)
```

- Agents run in their own process groups (`os.setsid`) for clean teardown
- Ctrl+C (SIGINT) terminates all child agents via `killpg`, not just the parent
- Output is live-tee'd to disk via reader threads — no in-memory buffering
- Retry attempts archive prior stdout/stderr before restarting

### Artifacts

Every invocation creates `/tmp/council-{pid}/` with:

```
codex.stdout          live tee of agent stdout
codex.stderr          live tee of agent stderr
codex.meta            one-line JSON state (rewritten on each transition)
codex.attempt1.stderr (preserved on retry)
gemini.stdout
gemini.stderr
gemini.meta
heartbeat.log         periodic status snapshots
```

The transcript file is deleted after completion (may contain sensitive session content). Agent artifacts are preserved for debugging.

### Security

- All CLI invocations use `subprocess.Popen` with list args (no shell) — shell injection at the subprocess level is structurally impossible
- The `pre_bash.py` hook blocks injection patterns (pipes, command substitution, dangerous redirects) in the outer bash layer
- Each agent's prompt explicitly instructs read-only behavior: no file creation, modification, or deletion
- Transcript files are cleaned up after completion

## Limitations

- **Snapshot, not stream.** cli-council captures the session state at invocation time. It doesn't support continuous context sharing or multi-phase workflows.
- **One-directional.** Other models analyze and respond, but can't act on the codebase.
- **CLI availability.** Each agent needs its CLI installed and authenticated. If a binary isn't on `$PATH`, that agent is skipped.
- **Token limits.** Long sessions produce large transcripts. `transcript_mode: file` removes the ARG_MAX bottleneck, but the receiving model's context window is still the limit.

## License

[MIT](LICENSE)
