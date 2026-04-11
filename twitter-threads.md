# Twitter Thread

**Tweet 1**

If you use Claude Code + Codex (or Gemini), you've hit this problem:

You're 30 minutes into a Claude Code session. You want another model to check your blind spots. But there's no way to give it the full context without manually re-explaining everything.

I fixed this.

**Tweet 2**

I tried the obvious approach first: Warp, left pane Claude Code, right pane Codex.

Warp promises block-level context sharing. But both agents run as full TUIs — they swallow Warp's UI hooks. No sparkles icon, no Cmd+↑ attachment, no right-click "attach as context."

The terminal can't help when the TUI eats its features.

**Tweet 3**

Then I noticed: Claude Code already saves every session as a .jsonl file. Every message, every tool call, every result — structured data, sitting right there.

The context I wanted to "share" was never locked inside the terminal. It was on disk the whole time.

**Tweet 4**

So I built cli-council: a Claude Code skill that reads the session file, builds a full transcript (conversation + CLAUDE.md + memory), and pipes it to Codex/Gemini/any CLI in parallel.

One command inside Claude Code:

/cli-council Does this approach have blind spots?

Both models respond with independent analysis, with full session context.

**Tweet 5**

The broader point: when we want "multi-agent collaboration," we reach for better terminals and orchestrators. But the bottleneck isn't layout — it's data flow.

An agent that reasoned for 30 minutes has accumulated thousands of tokens of context. That context is the valuable thing, not the window it's in.

**Tweet 6**

Install is two lines:

git clone https://github.com/Bobbyztz/cli-council .claude/skills/cli-council
pip install pyyaml

Config-driven — add any AI CLI in one YAML block. MIT licensed.

What's your workflow for getting second opinions across models? Curious how others handle this.

https://github.com/Bobbyztz/cli-council
