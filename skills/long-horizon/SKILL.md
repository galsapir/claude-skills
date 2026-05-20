---
name: long-horizon
description: >
  Transform a user's draft prompt into a long-horizon coding-agent task prompt.
  Use when the user asks to make a prompt long-horizon, turn something into a
  long-running agent task, add long-horizon scaffolding, or invokes
  "$long-horizon" or "/long-horizon". Appends framing for running far without
  unnecessary stops, using subagents for scoped background work, and maintaining
  implementation-notes.html with decisions, deviations, tradeoffs, and open
  questions.
license: MIT
metadata:
  author: galsapir
  version: "1.0.0"
---

# Long-Horizon Task Wrapper

Rewrite the user's draft prompt into a long-horizon task prompt for a coding agent.
The user's draft carries the task substance; this skill only adds the operating
scaffold that lets an agent keep working while the user is away.

## Workflow

1. Take the user's draft prompt as-is. Do not paraphrase, restructure, or formalize it.
2. Fix only obvious typos or small fluency issues that would distract the target agent.
3. Preserve the user's register. If they write lowercase/casual, keep it lowercase/casual.
   If they write formally, make the appended block formal too.
4. Bridge naturally from the draft into the long-horizon block. If the draft already
   starts this framing, continue it instead of restating it.
5. Append the long-horizon block from the template, adapting only where this file says to.
6. Output the full rewritten prompt as one fenced block for easy copy. Do not add commentary
   outside the fence unless the user asks.

If the user did not provide a draft prompt, ask for it. Do not invent the substantive task.

## Template

Append this after the user's draft:

```text
this is a long-horizon task. don't stop to ask unless you're blocked by credentials, destructive actions, external approvals, or something genuinely irreversible. otherwise, make the best reasonable decision, document it, and keep moving.

spawn small research subagents in the background for any questions that come up, and use subagents more broadly wherever you see fit: parallelizable work, scoped investigations, independent verification, anything that benefits from fresh context. keep each subagent task narrow, continue local work while they run, then integrate their findings. the subagent pattern is working well, keep using it. run as far as you can.

as you work, maintain a running `implementation-notes.html` file capturing anything i should know about how the implementation diverges from or interprets the spec:

- **Design decisions**: choices you made where the spec was ambiguous
- **Deviations**: places where you intentionally departed from the spec, and why
- **Tradeoffs**: alternatives you considered and why you picked what you did
- **Open questions**: anything you'd want me to confirm or revise
```

## Adaptation Rules

- **Voice**: Match the user's capitalization, directness, and level of polish. The default
  template is lowercase/casual because that is the common case for this skill.
- **Subagent sources**: If the draft names specific sources for questions, weave them into
  the subagent sentence. Example: "PR68 has the info, adva documents well and doesn't
  keep secrets, so use subagents to inspect that context first."
- **Existing long-horizon phrasing**: If the draft already says "this is another
  long-horizon task" or similar, do not duplicate that sentence. Continue with the missing
  pieces: decision-making, subagents, and notes.
- **Research or exploration tasks**: Keep `implementation-notes.html`, but rename the
  section meanings in the generated prompt if needed: "Design decisions" can become
  "Choices made"; "Deviations" can become "Direction changes"; "Open questions" stays.
- **No subagent tool**: Keep the subagent instruction in the output unless the user asks
  for a target agent that definitely lacks subagents. If adapting, say to maintain a
  background questions list and continue with documented assumptions.
- **Safety**: Do not remove the guardrail about credentials, destructive actions, external
  approvals, or irreversible decisions unless the user explicitly asks for that risk.

## Quality Bar

The final prompt should read like one coherent user instruction, not a pasted-on policy block.
It should increase autonomy without erasing accountability: the target agent should make
ordinary engineering decisions, keep evidence, and leave the user a clear trail in
`implementation-notes.html`.
