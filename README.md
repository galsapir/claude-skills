# skills

A collection of [Agent Skills](https://agentskills.io) by [Gal Sapir](https://github.com/galsapir). Some skills are inspired by or adapted from [Matt Pocock's skills](https://github.com/mattpocock/skills) (MIT).

Compatible with Claude Code, Cursor, GitHub Copilot, VS Code, Gemini CLI, and [many other agents](https://agentskills.io) that support the open Agent Skills standard.

## Install

```
npx skills add galsapir/skills
```

This installs all skills from the repository. To install a specific skill:

```
npx skills add galsapir/skills --skill interview
npx skills add galsapir/skills --skill long-horizon
npx skills add galsapir/skills --skill walkthrough-page
npx skills add galsapir/skills --skill adversarial-review
npx skills add galsapir/skills --skill ubiquitous-language
npx skills add galsapir/skills --skill paper-to-illustrated-video
```

## Update

```
npx skills update
```

## Skills

Skills are invoked by describing the task in natural language — the agent selects a matching skill based on its description. No slash command needed.

### `interview` — Project Interview & Design Grill

Deep project interview with two modes. **Discovery mode** uncovers requirements through structured questioning and produces a spec. **Grill mode** activates when you bring an existing plan or design — it stress-tests your decisions by walking the design tree branch by branch.

```
"use the interview skill to scope a CLI tool for managing dotfiles"
"interview me about adding dark mode to settings"
"grill me on this plan: path/to/plan.md"
"use the interview skill to stress-test my architecture doc"
```

### `long-horizon` — Long-Running Agent Prompt Wrapper

Turns a draft prompt into a long-horizon coding-agent task prompt. Adds scaffolding for autonomous progress, background subagents, and an `implementation-notes.html` decision trail.

```
"use long-horizon on this draft prompt: ..."
"make this a long-horizon task"
"/long-horizon turn this into a prompt i can hand to codex"
```

### `walkthrough-page` - Markdown-to-HTML Walkthrough Builder

Turns Markdown, source files, or a short interview into a polished static HTML walkthrough page with copyable commands, diagrams, checkpoints, and validation.

```
"use walkthrough-page to make an onboarding page for this repo"
"build a nice HTML walkthrough from docs/onboarding.md"
"turn this markdown into a polished static page"
"turn this CLI workflow into a copyable web walkthrough"
"make a one-page concept explainer for the evaluation pipeline"
```

### `adversarial-review` — Independent Second Opinion

Gets an independent second opinion on code, specs, diffs, or GitHub issues from a separate AI model. Supports multiple reviewer backends for genuinely orthogonal perspectives.

```
"run adversarial-review on src/main.py"
"adversarial-review src/main.py with the codex backend"
"adversarial-review my uncommitted changes"
"adversarial-review issue #42"
"adversarial-review PR #7"
"adversarial-review src/main.py (quick mode)"
```

The skill accepts these arguments: `[target] [--backend codex|claude|bedrock] [--model name] [--quick]`.

**Backends**:

| Backend | Default Model | Notes |
|---------|---------------|-------|
| `codex` | `gpt-5.4` | Most orthogonal — different model family |
| `claude` | `sonnet` | Same family, fresh context |
| `bedrock` | `claude-sonnet-4-6` | Same family via AWS; extensible to Llama/Nova/Mistral |

**Output structure**: Executive Summary (SHIP/ITERATE/RETHINK verdict), Understanding (full mode), Findings (severity + confidence rated), Strengths, Questions for Author.

The finding format uses [semi-formal reasoning](https://arxiv.org/abs/2603.01896) (Ugare & Chandra, 2026) — each finding is a certificate with explicit premises, execution trace, and derived conclusion.

### `ubiquitous-language` — Domain Glossary

Extracts a DDD-style ubiquitous language glossary from the current conversation. Flags ambiguities, proposes canonical terms, and saves to `UBIQUITOUS_LANGUAGE.md`. Adapted from [mattpocock/skills](https://github.com/mattpocock/skills).

```
"build a ubiquitous language from this conversation"
"define our domain terms"
"let's harden the terminology for this project"
```

### `paper-to-illustrated-video` — Paper to Illustrated Video

Turns a paper or benchmark release into one short silent announcement video (20-35 s, square, mobile-legible) that reads like a technical guide to the paper. Script checkpoint first, then a deterministic Pillow renderer with ffmpeg encoding, data-backed claim checks, an MP4 contract checker, contact sheet, poster, provenance, tests, and a PR.

```
"use paper-to-illustrated-video to make the X video for this preprint"
"turn figure 3 and the results tables into a 30-second illustrated video"
"paper in 30 seconds, no URL, sentence case"
```

Bundled: `assets/render_template.py` (renderer skeleton), `scripts/check_video.py` (MP4 box parser + claims + provenance checks), `references/script-checkpoint.md` (beat table, voice rules, worked example), `references/pitfalls.md`.

## Repository Structure

This repository follows the [Agent Skills specification](https://agentskills.io/specification):

```
skills/
  interview/
    SKILL.md              # Skill metadata + instructions
  long-horizon/
    SKILL.md              # Prompt wrapper for long-running agent tasks
  walkthrough-page/
    SKILL.md              # Interview + static walkthrough workflow
    assets/
      walkthrough-template.html
    scripts/
      markdown_inventory.py
      validate_page.py
  adversarial-review/
    SKILL.md              # Skill metadata + instructions
    references/
      review-prompt.md    # Review prompt template
    scripts/
      bedrock-review.py   # AWS Bedrock backend script
  ubiquitous-language/
    SKILL.md              # Skill metadata + instructions
  paper-to-illustrated-video/
    SKILL.md              # Script checkpoint + renderer + checks workflow
    assets/
      render_template.py  # Deterministic Pillow renderer skeleton
    scripts/
      check_video.py      # MP4 contract, claims, and provenance checker
    references/
      script-checkpoint.md
      pitfalls.md
```

Each skill is a self-contained directory with a `SKILL.md` file containing YAML frontmatter (`name`, `description`, and optional fields) followed by Markdown instructions.

## Migrating from the Plugin Marketplace

If you previously installed using the old Claude Code plugin marketplace format:

```
/plugin uninstall gal-skills
```

Then reinstall using the skills CLI:

```
npx skills add galsapir/skills
```

## Prerequisites

- **Codex backend**: `npm install -g @openai/codex` + `codex auth`
- **Bedrock backend**: AWS credentials configured with Bedrock access in `eu-west-1`
- **Claude backend**: Claude Code CLI (you already have this)

## License

MIT
