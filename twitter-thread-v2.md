# Twitter Thread — v2 update

**Tweet 1**

Two weeks ago I shipped cli-council: one command inside Claude Code to get independent analysis from Codex + Gemini, with full session context.

Since then I've run ~50 council audits on real research work. Every pain point became a feature. Here's what changed.

github.com/Bobbyztz/cli-council

**Tweet 2**

Problem #1: You invoke the council. One agent hits a rate limit. The whole run blocks. You re-run manually, hoping it works this time.

Now: quota errors are auto-classified and that agent is gracefully skipped. The other agent still runs. Network errors retry with exponential backoff. All config-driven — zero code changes needed.

**Tweet 3**

Problem #2: Both agents are running. You wait 3 minutes staring at a blank terminal. Are they working? Stuck? Dead?

Now: a heartbeat thread prints status every 30 seconds — which agent is running, how many bytes of output so far, elapsed time. From another terminal: `tail -F /tmp/council-*/*.stdout` to watch agents think in real time.

**Tweet 4**

Problem #3: An agent fails at minute 4 of a 5-minute run. The error message is gone. You have nothing to debug with.

Now: every agent gets its own artifact directory under `/tmp/council-{pid}/`. Live-tee'd stdout, stderr, and a JSON meta file tracking state transitions. Retry attempts are archived as `agent.attempt1.stderr` so you never lose evidence.

**Tweet 5**

Problem #4 (the subtle one): I noticed Gemini kept agreeing with Claude's analysis instead of catching blind spots. It was reading the transcript's paraphrases and inheriting them — second-hand review.

Two fixes:

A "primary-source grounding protocol" that forces every agent to read the actual files referenced in the session, not just the transcript's excerpts.

And an anti-sycophancy prompt prefix for Gemini that reframes the task: "this work is flawed in ways the participants did not catch — find what they missed." Uses the agreement bias as fuel instead of fighting it.

**Tweet 6**

Problem #5: Long sessions produce massive transcripts. Gemini CLI passes the prompt as a CLI argument — hit ARG_MAX at ~1MB.

Now: per-agent `transcript_mode` in config. Set `file` and the transcript stays on disk; the agent reads it via tool call. No size limit. Codex still gets inline mode (works better for its sandbox).

**Tweet 7**

The audit output now has machine-readable status:

- AUDIT_FULL — all agents completed
- AUDIT_PARTIAL_QUOTA — some agents quota-skipped, rest completed (still valid)
- AUDIT_BLOCKED — real failure, can't substitute self-review

This matters because in my workflow, the council gates decisions. BLOCKED means stop, not "just use your own judgment."

**Tweet 8**

Under the hood: the runner is now a proper process manager.

Each agent is an AgentProc with a state machine (pending → starting → running → completed/timeout/error/skipped). Process groups for clean SIGINT teardown. Ctrl+C kills all child agents, not just the parent.

1014 lines, still one file, still zero dependencies beyond PyYAML.

**Tweet 9**

All error classification is regex-driven from config.yaml. Rate limits, network failures, gateway errors — add a pattern, change the behavior. No code changes.

```yaml
error_patterns:
  quota:
    - "rate.?limit"
    - "\\b429\\b"
    - "too many requests"
  network:
    - "connection refused"
    - "dns.*(fail|error|lookup)"
```

**Tweet 10**

The meta-lesson from 50 runs: multi-model review is only useful if the models actually disagree. That means fighting sycophancy, forcing primary-source reading, and making failures visible instead of silent.

The hard part of multi-agent tooling isn't orchestration. It's making each agent genuinely independent.

github.com/Bobbyztz/cli-council
