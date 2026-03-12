# claude-skills

Personal Claude Code plugin marketplace by [Gal Sapir](https://github.com/galsapir).

## Install

Add the marketplace and install the plugins you want:

```
/plugin marketplace add galsapir/claude-skills
/plugin install interview@gal-skills
/plugin install adversarial-review@gal-skills
```

## Plugins

### `/interview` — Project Interview

Deep project interview that produces actionable specs before implementation begins. Conducts a structured requirements interview with adaptive depth and checkpoints, then outputs a spec as a file, GitHub issue, or both.

```
/interview                                    # starts with "what are we building?"
/interview a CLI tool for managing dotfiles
/interview path/to/plan.md                   # reads a plan file as starting point
```

### `/adversarial-review` — Independent Second Opinion

Gets an independent second opinion on code, specs, diffs, or GitHub issues from a separate AI model. Supports multiple reviewer backends for genuinely orthogonal perspectives.

```
/adversarial-review src/main.py                          # auto-detect backend
/adversarial-review src/main.py --backend codex          # use Codex (GPT family)
/adversarial-review src/main.py --backend claude          # use claude -p
/adversarial-review src/main.py --backend bedrock         # use AWS Bedrock
/adversarial-review diff                                  # review uncommitted changes
/adversarial-review #42                                   # review GitHub issue
/adversarial-review PR #7                                 # review pull request
/adversarial-review src/main.py --quick                   # skip Understanding section
/adversarial-review src/main.py --model gpt-5.4          # explicit model
```

**Backends**:

| Backend | Default Model | Notes |
|---------|---------------|-------|
| `codex` | `gpt-5.4` | Most orthogonal — different model family |
| `claude` | `sonnet` | Same family, fresh context |
| `bedrock` | `claude-sonnet-4-6` | Same family via AWS; extensible to Llama/Nova/Mistral |

**Output structure**: Executive Summary (SHIP/ITERATE/RETHINK verdict), Understanding (full mode), Findings (severity + confidence rated), Strengths, Questions for Author.

## Prerequisites

- **Codex backend**: `npm install -g @openai/codex` + `codex auth`
- **Bedrock backend**: AWS credentials configured with Bedrock access in `eu-west-1`
- **Claude backend**: Claude Code CLI (you already have this)

## License

MIT
