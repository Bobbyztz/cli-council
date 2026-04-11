# Twitter Threads

## Thread 1: The Problem Thread

**Tweet 1 (hook)**

I spent an hour trying to get Codex to review my Claude Code session.

Tried Warp (left-right split), Conductor (worktree handoff), cmux (pane management).

None of them worked.

The actual problem was embarrassingly simple.

**Tweet 2**

Here's what I wanted:

I'm deep in a Claude Code session — we've discussed a design, read files, made 20 decisions. Now I want Codex (or Gemini) to check my blind spots.

The obvious move: open another terminal, start Codex, and... re-explain everything from scratch.

**Tweet 3**

So I tried the "AI terminal" tools everyone recommends:

Warp: "Use the sparkles icon to attach blocks as context"
Me: There is no sparkles icon. Claude Code's TUI swallowed it.

Warp: "Try Cmd+↑ to attach blocks"
Me: That just turns the block blue. Codex's TUI ate the shortcut.

**Tweet 4**

Conductor: "One-click handoff between agents with worktree isolation"

Sounds great — except it's a whole orchestration layer for what should be a simple data transfer.

cmux: Great notification ring. But for context sharing? Same story — you end up manually exporting a file.

**Tweet 5**

After all that, the "solution" was:

1. Ask Claude Code to export the full conversation to FULL_CONTEXT.md
2. Tell Codex to read FULL_CONTEXT.md

That's it. Nothing to do with Warp, Conductor, or cmux. Just two CLI tools reading a file.

**Tweet 6**

The real problem was never about terminals.

It's about data: how do you transfer one agent's full accumulated context to another, losslessly, without manual intervention?

Every "multi-agent terminal" is solving the wrong layer — topology (how to arrange windows) instead of memory (how to share context).

**Tweet 7**

So I built cli-council.

It reads Claude Code's native session data (.jsonl), builds a transcript with full project context, and feeds it to Codex/Gemini/any CLI in parallel.

One command. Full context. No manual export.

github.com/Bobbyztz/cli-council

---

## Thread 2: The How-It-Works Thread

**Tweet 1 (hook)**

"How do you get a second opinion from another AI model mid-session?"

Not by copy-pasting. Not by re-explaining. Not by buying a fancy terminal.

By reading the data that already exists.

**Tweet 2**

Claude Code stores every session as a .jsonl file:
- Every user message
- Every assistant response  
- Every tool call and result
- Full project context

This file IS the conversation. It's already there. You just need to read it.

**Tweet 3**

cli-council does exactly that:

```
Session .jsonl → extract conversation → add CLAUDE.md + memory → send to Codex/Gemini in parallel → labeled output
```

6 files. ~650 lines. One Python dependency (pyyaml).

**Tweet 4**

Usage:

```
/cli-council Is this migration plan safe?
```

Output:

```
═══════════════════════
  Codex (GPT-5.4)
═══════════════════════
The plan misses concurrent writes during backfill...

═══════════════════════
  Gemini 3.1 Pro  
═══════════════════════
Two concerns. First, the rollback strategy...
```

**Tweet 5**

It auto-detects two modes:

Early conversation (no assistant replies yet) → parallel thinking: each model independently analyzes your question with project context

Mid-conversation → session review: each model reviews the full Claude Code session and gives independent feedback

**Tweet 6**

Config-driven. Add any CLI that takes a text prompt:

```yaml
agents:
  codex:
    enabled: true
    binary: codex
    args_before: [exec, --sandbox, read-only, --full-auto]
  gemini:
    enabled: true
    binary: gemini
    args_before: [-m, gemini-3.1-pro-preview]
```

Binary not on $PATH? Silently skipped. No crashes.

**Tweet 7**

Install:

```bash
git clone github.com/Bobbyztz/cli-council .claude/skills/cli-council
pip install pyyaml
```

Claude Code auto-discovers it. That's the whole setup.

MIT licensed. github.com/Bobbyztz/cli-council

---

## Thread 3: The Insight Thread

**Tweet 1 (hook)**

Every "multi-agent AI terminal" in 2026 is solving the wrong problem.

They're all building better containers. Nobody is solving context transfer.

**Tweet 2**

The current landscape:

- Warp: GPU-accelerated terminal + AI blocks
- Conductor: worktree isolation + review panels  
- cmux: Ghostty-native + notification rings
- Superset: multi-agent orchestration + browser

All impressive engineering. All focused on: how do I arrange multiple AI agents on screen?

**Tweet 3**

But the actual user need is:

"I've been talking to Claude Code for 30 minutes. I want Codex to see everything we discussed and tell me what I'm missing."

This is a data problem, not a layout problem.

**Tweet 4**

When you run Claude Code + Codex side by side in any of these tools, the context sharing breaks down to one of:

1. Manual: copy-paste or export to file
2. Non-existent: each agent starts from zero
3. Lossy: summaries that drop critical details

The terminal chrome doesn't help.

**Tweet 5**

The fix is obvious in retrospect:

Claude Code already stores every conversation as structured data (.jsonl). Read it. Transform it. Pipe it to another model.

No UI layer needed. The data was always there.

**Tweet 6**

This is a broader pattern in AI tooling:

We keep building UI wrappers when the bottleneck is data flow.

The agent that just spent 30 minutes reasoning has accumulated context worth thousands of tokens. Losing that context when you switch models is the real cost — not the terminal you're using.

**Tweet 7**

I built cli-council to solve this for myself. One command, full session context, parallel execution across models.

But the deeper point: if you're building multi-agent tools, think about the memory layer, not just the topology layer.

github.com/Bobbyztz/cli-council
