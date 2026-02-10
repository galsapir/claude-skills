---
name: adversarial-review
description: >
  Get an independent second opinion from a separate AI model on code, specs,
  diffs, PRs, or GitHub issues. Use when the user asks for "second opinion",
  "adversarial review", "independent review", or "codex review". Supports
  codex (GPT family), claude -p, and AWS Bedrock backends.
  Arguments: [target] [--backend codex|claude|bedrock] [--model name] [--quick]
allowed-tools: Bash(codex:*) Bash(claude:*) Bash(gh:*) Bash(git:*) Bash(uv:*) Read Grep Glob
---

Independent second opinion from a separate AI model.

## Workflow

### 1. Detect Target

Parse `$ARGUMENTS`:

- File path(s) → code review
- `diff` / `changes` → `git diff` review
- `#N` or issue URL → `gh issue view` review
- PR URL or `PR #N` → `gh pr view` + `gh pr diff` review
- No args → ask user via AskUserQuestion

Extract flags: `--backend`, `--model`, `--quick`.

### 2. Reconnaissance

Gather context before building the review prompt:

1. Read the target (files, diff, issue, or PR)
2. Identify related files (imports, tests, config) and project context (README, CLAUDE.md)
3. Assemble a 2-5 sentence context summary: what the project does, what the target accomplishes, key related files

### 3. Select Backend

Priority: explicit `--backend` flag > auto-detect.

Auto-detect: try `codex` (`which codex`) → `bedrock` (script exists) → `claude` (fallback).

Default models: codex=`o4-mini`, claude=`sonnet`, bedrock=`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`. Override with `--model`.

### 4. Build Review Prompt

Read [references/review-prompt.md](references/review-prompt.md) and substitute placeholders:

- `{{CONTENT_TYPE}}` → code, spec, diff, issue, pr
- `{{REVIEW_TARGET}}` → file paths or inline content
- `{{CONTEXT}}` → project/architectural context from step 2
- `{{MODE}}` → `full` (default) or `quick` (if `--quick` flag or user said "delegate"/"just review")
- `{{GUIDANCE}}` → focus areas, related test files, key dependencies

Write assembled prompt to `/tmp/ar-prompt-$$.md`.

### 5. Execute Review

Capture git state before (`git diff --stat`), then run:

- **codex**: `codex exec "$(cat /tmp/ar-prompt-$$.md)" --sandbox read-only --model <model>` (use stdin for prompts >100KB)
- **claude**: `claude -p "$(cat /tmp/ar-prompt-$$.md)" --model <model> --output-format text`
- **bedrock**: `uv run scripts/bedrock-review.py /tmp/ar-prompt-$$.md --model <model> --region eu-west-1`

After execution, run `git diff --stat && git status --short`. If any new changes appear, flag immediately.

### 6. Present Results

Output verbatim as:

```
## Independent Review (via [backend] / [model])
[full response]
```

Do NOT editorialize or soften. If you disagree with a finding, add a labeled note after the full review. Clean up temp file.
