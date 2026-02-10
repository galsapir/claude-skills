---
name: adversarial-review
description: >
  Get an independent second opinion from a separate AI model.
  Use when the user asks for "second opinion", "adversarial review",
  "independent review", or "codex review" on code, specs, diffs, PRs,
  or GitHub issues.
argument-hint: "[target] [--backend codex|claude|bedrock] [--model name] [--quick]"
allowed-tools: Bash(codex *), Bash(claude *), Bash(gh *), Bash(git diff*), Bash(git log*), Bash(git status*), Bash(uv run*), Read, Grep, Glob
disable-model-invocation: true
---

Get an independent second opinion on code, specs, diffs, or issues from a separate AI model.

## Phase 1: Detect Target

Parse `$ARGUMENTS` to determine what to review:

- **File path(s)** (e.g., `src/main.py`, `lib/*.ts`) → code/spec review
- **`diff` or `changes`** → review uncommitted changes via `git diff`
- **`#N` or GitHub issue URL** → issue review via `gh issue view`
- **PR URL or `PR #N`** → PR review via `gh pr view` and `gh pr diff`
- **No arguments** → ask the user what to review using AskUserQuestion

Extract flags from arguments:
- `--backend codex|claude|bedrock` → explicit backend choice
- `--model <name>` → explicit model override
- `--quick` → skip Understanding section in output

## Phase 2: Reconnaissance

Before sending anything to the reviewer, gather context yourself:

1. **Read the target**:
   - For files: read each target file
   - For diffs: run `git diff` (unstaged) and `git diff --cached` (staged)
   - For PRs: run `gh pr diff <number>` and `gh pr view <number>`
   - For issues: run `gh issue view <number>` including comments

2. **Identify related context** the reviewer should know about:
   - Check imports/dependencies of target files
   - Find related test files (glob for `test_*`, `*_test.*`, `*.spec.*`)
   - Read project README or CLAUDE.md if they exist (for project conventions)
   - For diffs/PRs: identify which modules are affected

3. **Assemble a context summary** (2-5 sentences):
   - What the project does
   - What the target code/change is trying to accomplish
   - Key files the reviewer should examine

## Phase 3: Select Backend and Model

**Priority**: explicit `--backend` flag > auto-detect availability.

**Auto-detect order**:
1. `codex` — check if `codex` CLI is available (`which codex`)
2. `bedrock` — check if wrapper script exists at the expected path
3. `claude` — fallback, always available (uses `claude -p`)

**Default models per backend**:

| Backend | Default model |
|---------|--------------|
| codex | `o4-mini` |
| claude | `sonnet` |
| bedrock | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` |

If `--model` is provided, use it for the selected backend.

## Phase 4: Detect Review Mode

- Default: **full mode** (include Understanding section in output)
- If `--quick` flag is present, or the user said "delegate"/"skip understanding"/"just review": **quick mode**

## Phase 5: Build Review Prompt

Read the prompt template from `review-prompt.md` (located in the same directory as this SKILL.md).

Substitute these placeholders in the template:

| Placeholder | Value |
|-------------|-------|
| `{{CONTENT_TYPE}}` | `code`, `spec`, `diff`, `issue`, or `pr` |
| `{{REVIEW_TARGET}}` | For files: file paths + instruction to read them. For diffs/issues/PRs: the actual inline content. |
| `{{CONTEXT}}` | Project description, related file paths, architectural notes from Phase 2 |
| `{{MODE}}` | `full` or `quick` |
| `{{GUIDANCE}}` | Specific areas to focus on, related test files, key dependencies |

Write the assembled prompt to a temp file at `/tmp/ar-prompt-$$.md`.

## Phase 6: Execute Review

**IMPORTANT**: Before executing, capture current git state:
```bash
git rev-parse HEAD 2>/dev/null
git diff --stat 2>/dev/null
```

Run the review based on selected backend:

| Backend | Command |
|---------|---------|
| codex | `codex exec "$(cat /tmp/ar-prompt-$$.md)" --sandbox read-only --model <model>` |
| claude | `claude -p "$(cat /tmp/ar-prompt-$$.md)" --model <model> --output-format text` |
| bedrock | `uv run skills/adversarial-review/scripts/bedrock-review.py /tmp/ar-prompt-$$.md --model <model> --region eu-west-1` |

**If the prompt is very large** (the temp file exceeds 100KB), for codex backend use stdin instead:
```bash
codex exec --sandbox read-only --model <model> < /tmp/ar-prompt-$$.md
```

**Post-execution safety check** (for all backends):
```bash
git diff --stat
git status --short
```
If ANY uncommitted changes appear that weren't there before, **immediately flag this to the user** and show what changed. Do NOT silently continue.

## Phase 7: Present Results

Output the reviewer's response verbatim inside a clearly labeled section:

```markdown
## Independent Review (via [backend] / [model])

[reviewer's full response here]
```

**Rules for presenting results**:
- Do NOT editorialize, soften, or rephrase the review
- Do NOT apologize for harsh findings
- If you (Claude) genuinely disagree with a specific finding, add a brief labeled note AFTER the full review:
  ```
  > **Claude's note on [finding]**: [brief disagreement with reasoning]
  ```
- If the review was in quick mode, note this: "*(Quick mode — Understanding section omitted)*"

Clean up: remove the temp prompt file.
