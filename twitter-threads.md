# Twitter Threads

## Thread 1: The Problem Thread

**Tweet 1 (hook)**

I tried to get Codex to review my Claude Code session in Warp.

Left pane: Claude Code. Right pane: Codex. Should be simple.

It wasn't. And the reason surprised me.

**Tweet 2**

Here's what I wanted:

I'm deep in a Claude Code session — we've discussed a design, read files, made 20 decisions. Now I want Codex to check my blind spots.

The obvious move: open another terminal, start Codex, and... re-explain everything from scratch.

**Tweet 3**

Warp promises block-level context sharing between panes. Sounds perfect.

"Use the sparkles icon to attach blocks as context"
→ No sparkles icon. Claude Code's TUI hides Warp's block decorations.

"Try Cmd+��� to attach blocks"
→ Just turns the block blue. Codex's TUI captures the shortcut.

Right-click menu? No "attach as context" option either.

**Tweet 4**

After trying every suggested shortcut and menu, the final "solution" was:

1. Ask Claude Code to export the conversation to FULL_CONTEXT.md
2. Tell Codex to read FULL_CONTEXT.md

Just two CLI tools reading a file. Nothing to do with Warp at all.

**Tweet 5**

This made me realize: the problem was never about the terminal.

It's about data — how do you transfer one agent's full accumulated context to another, losslessly, without manual intervention?

When both agents run as TUIs, the terminal's UI features get swallowed. The context sharing layer needs to work below the UI.

**Tweet 7**

So I built cli-council.

It reads Claude Code's native session data (.jsonl), builds a transcript with full project context, and feeds it to Codex/Gemini/any CLI in parallel.

One command. Full context. No manual export.

https://github.com/Bobbyztz/cli-council

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
git clone https://github.com/Bobbyztz/cli-council .claude/skills/cli-council
pip install pyyaml
```

Claude Code auto-discovers it. That's the whole setup.

MIT licensed. https://github.com/Bobbyztz/cli-council

---

## Thread 3: The Insight Thread

**Tweet 1 (hook)**

I ran Claude Code and Codex side by side in Warp. The context sharing features didn't work — both TUIs swallowed the terminal's UI hooks.

This made me think about what "multi-agent context sharing" actually requires.

**Tweet 2**

The user need is simple:

"I've been talking to Claude Code for 30 minutes. I want Codex to see everything we discussed and tell me what I'm missing."

Most tools frame this as a layout problem — split panes, tabs, worktrees. But it's a data problem.

**Tweet 3**

When both agents run as full TUIs inside a terminal, UI-level features (block attachment, sparkles icons, keyboard shortcuts for context sharing) get captured by the TUI before the terminal sees them.

The context sharing layer can't live in the terminal UI. It needs to work at the data level.

**Tweet 4**

The fix is obvious in retrospect:

Claude Code already stores every conversation as structured data (.jsonl). Every message, tool call, and result — already there.

Read it. Transform it. Pipe it to another model. No UI layer needed.

**Tweet 5**

This is a pattern worth noticing in AI tooling:

We keep building better containers (terminals, orchestrators, pane managers) while the bottleneck is data flow between agents.

An agent that spent 30 minutes reasoning has accumulated context worth thousands of tokens. That context is the valuable thing — not the window it's displayed in.

**Tweet 6**

I built cli-council to solve this for myself. One command, full session context, parallel execution across models.

But the broader point: if you're building multi-agent tools, the memory layer (how agents share accumulated context) matters more than the topology layer (how you arrange them on screen).

https://https://github.com/Bobbyztz/cli-council
