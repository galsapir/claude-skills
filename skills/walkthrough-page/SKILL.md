---
name: walkthrough-page
description: >
  Create polished static HTML walkthrough, onboarding, explainer, or concept pages
  from Markdown, source files, or a short interview. Use when the user wants to
  turn .md docs into a good-looking HTML page; create a useful human-facing web
  page for understanding a codebase, workflow, design, paper, CLI, evaluation
  concept, or project onboarding; or asks for a walkthrough page, onboarding page,
  interactive explainer, one-page demo, copyable command guide, or concept map.
  Starts with adaptive interview checkpoints, then builds a single-file static page
  with accurate commands, expected outputs, diagrams or inspectors, and validation.
---

# Walkthrough Page

Create a static HTML page that helps a human understand and rehearse a concept.
The output is a usable walkthrough, not a marketing page.

## Workflow

1. Gather context.
   - Read the user's prompt, linked/source files, repo instructions, README/docs, and any existing page to update.
   - If the source is Markdown, run `scripts/markdown_inventory.py` on it first to extract headings, code blocks, checklists, and links.
   - If the page teaches a code workflow, inspect the relevant code and runnable commands before describing them.
   - If the user points at an existing artifact, treat it as source material, not final structure.
   - Do not render Markdown 1:1 unless the user asks. Reshape it into a better teaching surface.

2. Run a short interview.
   - Ask 1-2 questions at a time.
   - Start with the highest-leverage unknowns: audience, desired outcome, source of truth, workflow to rehearse, commands/artifacts to include, and target path.
   - Prefer concrete questions: "what should the reader be able to do after 5 minutes?" beats "what level of detail?"
   - For Markdown inputs, ask what the HTML should make easier than the Markdown: skim, run commands, see structure, compare choices, or teach a concept.
   - After 3-5 questions, checkpoint: summarize what is established in 2-3 sentences, list remaining areas, and ask whether to continue, go higher level, skip to a section, or build now.
   - Use the host question tool if available. If not, ask in chat.
   - If the user says "delegate", "just do it", or gives enough detail, proceed with explicit assumptions.

3. Choose the teaching spine.
   Use the smallest set of sections that makes the page useful:
   - What this is and why it exists.
   - The mental model or skeleton.
   - A 30-90 second runnable path.
   - Anatomy of the main config/object/process.
   - Real-data or real-world path.
   - What happens under the hood.
   - Outputs/artifacts and how to inspect them.
   - Troubleshooting and next steps.

4. Build the page.
   - Default to a single static HTML file at `docs/<slug>/index.html` when the repo has `docs/`; otherwise use `walkthroughs/<slug>/index.html` or the user's requested path.
   - Copy and adapt `assets/walkthrough-template.html` when starting from scratch.
   - Keep it dependency-free by default: inline CSS and JS, no build step, no CDN, no external fonts.
   - Add two `ABOUTME:` lines at the top of generated code files.
   - Use real commands and real file paths. Run safe commands when practical. Expected output must come from actual output or be labeled "example output".
   - Put copy buttons on command blocks.
   - Include at least one visual explanation when it helps: flow diagram, inspector, anatomy table, tabs, or checkpoint checklist.
   - Make interactions teach something. Do not add animation or controls that only decorate.

5. Validate.
   - Run `python <skill-dir>/scripts/validate_page.py <path-to-index.html>`.
   - Manually inspect the page in a browser or with available screenshot tooling.
   - Check desktop and mobile widths for overflow, clipped buttons, overlapping text, and unreadable code.
   - Verify all copy buttons target existing code blocks.
   - Verify no placeholders, stale examples, or unverified claims remain.

6. Deliver.
   - Report the page path.
   - State what validation ran.
   - Give the local file path or dev-server URL only if needed.
   - Ask for walkthrough feedback only after the page exists.

## Interview Prompts

Start with a compact version of these, adapted to what is already known:

- Who is the reader, and what do they already know?
- What should they be able to do after using the page?
- What is the core mental model they need?
- What commands, files, or artifacts must be copyable or inspectable?
- If starting from Markdown, what should change: structure only, visual hierarchy, examples, diagrams, command blocks, or all of these?
- What level should this target: skim, working walkthrough, or deep dive?
- Where should the page live?

Checkpoint wording:

```text
Checkpoint: I have pinned down <audience/outcome/source material>. Remaining areas: <commands/visuals/depth/path>. Continue at this depth, go higher level, skip to a specific area, or build now?
```

## Page Quality Rules

- Prefer dense, calm, utilitarian pages over landing-page composition.
- Do not make a hero marketing page. The first screen should immediately teach the subject.
- Use cards only for repeated items, command panels, or genuinely framed tools. Do not nest cards.
- Keep typography restrained. Use hero-sized text only for the page title.
- Avoid decorative blobs, gradient orbs, stock imagery, and one-note palettes.
- Use responsive constraints for diagrams, code blocks, grids, and buttons.
- Make code horizontally scroll inside its block rather than pushing the page wider.
- Keep labels short. Button text must fit at mobile width.
- Support keyboard focus and reduced motion.
- Prefer inline SVG/HTML diagrams for concepts that need structure.
- Do not invent polish at the expense of accuracy.

## Static Page Template

Use `assets/walkthrough-template.html` as the starting point for new pages.

The template includes:

- Single-file HTML/CSS/JS.
- Copyable command blocks.
- Responsive section layout.
- A simple concept map.
- An inspector pattern for "click a node, read its role".
- Accessibility and mobile defaults.

Replace every sample string before validating. The template is intentionally invalid until adapted; run `validate_page.py` on the derived page, not on `assets/walkthrough-template.html`. Keep only the structural patterns that serve the user's topic.

## Markdown Inventory Script

For `.md` sources, run:

```bash
python /path/to/walkthrough-page/scripts/markdown_inventory.py docs/source.md --pretty
```

Use the output to find the teaching spine, reusable command blocks, and links worth preserving. The inventory is a planning aid, not a converter.

## Validation Script

Run:

```bash
python /path/to/walkthrough-page/scripts/validate_page.py docs/<slug>/index.html
```

The script checks basic static-page integrity. Passing it is necessary, not sufficient. Still inspect the page visually and verify the content.
