---
description: Deep project interview before starting implementation
argument-hint: [brief project description or plan file path]
model: opus
---

Conduct a thorough project interview to produce a clear, actionable spec before any implementation begins.

## Context Gathering

First, gather context about the current state:

1. Check if this is an existing project or greenfield:
   - Read the current directory structure (use `ls` and check for package.json, pyproject.toml, go.mod, CLAUDE.md, README, etc.)
   - If a git repo exists, check recent commits for context
   - If a CLAUDE.md exists, read it for project conventions
2. If `$ARGUMENTS` references a file path, read that file as the initial plan/idea
3. If `$ARGUMENTS` is a text description, use it as the starting point
4. If no arguments provided, ask what the project/feature is about

## Interview Process

Interview the user about their project using AskUserQuestion. The goal is to uncover requirements, constraints, edge cases, and design decisions that the user hasn't thought through yet.

### Question Design Principles

- Ask non-obvious questions. Don't ask things the user has already stated or that are self-evident.
- Probe for hidden complexity, unstated assumptions, and edge cases.
- Adapt question depth to project complexity — a weekend hack needs 10 questions, not 75.
- Prefer multiple-choice options when possible (with "Other" always available), but use open-ended questions when the answer space is too broad for predefined options.
- Ask 1-2 questions per AskUserQuestion call. Group related questions together.
- Frame questions around concrete scenarios ("What happens when a user tries to X while Y is happening?") rather than abstract concepts.

### Question Categories

Cover these areas as relevant to the project. Skip categories that clearly don't apply:

**Core Vision & Scope**
- What problem does this solve? Who is it for?
- What's the MVP vs nice-to-have?
- What does "done" look like?

**User Experience & Behavior**
- Key user flows and interactions
- Error states and edge cases from the user's perspective
- What happens when things go wrong?

**Technical Architecture**
- Tech stack choices (if not already decided)
- Data model and storage
- External dependencies and integrations
- Performance requirements and constraints

**Operational Concerns**
- Deployment and infrastructure
- Monitoring, logging, error handling
- Security considerations

**Project Constraints**
- Timeline and resource constraints
- Existing code/systems to integrate with
- Hard requirements vs flexible preferences

### Checkpoint Mechanism

After every 3-5 questions, present a checkpoint using AskUserQuestion:

```
Question: "Checkpoint: I've covered [areas covered so far]. Remaining areas to explore: [remaining areas]. How should we proceed?"
Options:
- "Continue at this depth" — keep going with detailed questions
- "Go higher level" — switch to broader, fewer questions for remaining areas
- "Skip to [specific area]" — jump to a particular topic
- "Wrap up" — enough info, generate the spec now
```

At each checkpoint, briefly summarize what has been established so far (2-3 sentences max) before asking how to proceed.

If the user says "wrap up" or "go higher level", respect that immediately. Don't sneak in extra detailed questions.

### Adaptive Depth

Gauge project complexity from the initial description and context:

- **Small feature/bugfix**: 5-10 questions, 1-2 checkpoints
- **Medium feature**: 10-20 questions, 2-3 checkpoints
- **Large project/system**: 20-40 questions, 4-6 checkpoints
- **Greenfield application**: 30-50+ questions, 5-8 checkpoints

State the estimated scope at the start: "This seems like a [size] project. I'll aim for roughly [N] questions across [M] checkpoints. We can always adjust."

## Spec Generation

When the interview is complete (either all areas covered or user says "wrap up"):

1. Synthesize all answers into a structured spec document
2. Use this format:

```markdown
# [Project/Feature Name] — Spec

## Overview
[2-3 sentence summary of what this is and why it exists]

## Goals & Non-Goals
### Goals
- [Concrete, measurable goals]

### Non-Goals
- [Explicitly out of scope items]

## User Stories / Key Flows
- As a [who], I want to [what], so that [why]
- [Key interaction flows described concretely]

## Technical Design
### Architecture
[High-level architecture decisions]

### Data Model
[Key entities and relationships, if applicable]

### API / Interface Design
[Endpoints, function signatures, or UI components, if applicable]

### Dependencies
[External services, libraries, tools]

## Edge Cases & Error Handling
- [Identified edge cases and how to handle them]

## Open Questions
- [Anything that came up during the interview that wasn't fully resolved]

## Implementation Notes
- [Key technical decisions, constraints, or preferences from the interview]
```

3. Adapt the template — skip sections that don't apply, add sections that do.

## Output Delivery

After generating the spec, ask the user with AskUserQuestion:

```
Question: "Spec is ready. Where should I put it?"
Options:
- "Write to file" — write spec to a file in the current directory (will ask for filename)
- "Create GitHub issue" — create a GH issue with the spec content
- "Both" — file + GH issue
- "Just show me" — display in chat, don't write anywhere
```

If writing to file: suggest a filename like `spec-[project-name].md` and confirm before writing.
If creating GH issue: use `gh issue create` with the spec as the body. Ask for labels/milestone if the repo uses them.

## Important

- This is an INTERVIEW, not a lecture. Listen more than you talk.
- Don't inject your own architectural opinions unless asked. Surface tradeoffs and let the user decide.
- If the user gives a one-word answer, that's fine. Don't push for more unless the answer is genuinely ambiguous.
- Keep checkpoint summaries SHORT. The user doesn't want to re-read everything they just told you.
- Never start implementing. This command produces a spec, nothing more.
