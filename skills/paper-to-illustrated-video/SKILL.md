---
name: paper-to-illustrated-video
description: >
  Turn a scientific paper, preprint, or benchmark release into one short silent
  announcement video (20-35 s, square, mobile-legible) that reads like a technical
  guide to the paper rather than a promo. Use when the user wants an illustrated
  video, animated figure, X/Twitter or LinkedIn video for a paper, a "paper in 30
  seconds" clip, or a reproducible video built from the repository's own figures
  and result tables. Covers the script checkpoint, voice rules, data-backed claim
  checks, a deterministic Pillow renderer with ffmpeg encoding, an MP4 contract
  checker, contact sheet, poster, provenance, tests, and the PR.
---

# Paper to Illustrated Video

Produce one coherent video whose every on-screen statement is traceable to the paper's own
tables, and whose viewer feels they captured the paper's important bits, not that they watched an ad.

## Workflow

1. Gather the sources before proposing anything.
   - Read the abstract, results, the announcement thread if one exists, and any claim-check
     document that maps statements to canonical sources. The thread's wording is the approved
     wording; reuse it for scoped findings.
   - Locate the figure sources and the aggregate result tables (CSV) behind each figure. Prefer
     tables over re-reading numbers off a figure. Never read participant-level files.
   - Extract the visual language from existing assets: palette hex values, font, card and
     header styles. Reuse them; do not invent a look.
   - Check whether figures are vector or a single rasterised image (AI-generated panels are
     often one raster). That decides whether elements can be redrawn or must be cropped.
   - Read two recent pieces of the author's own writing before drafting any text in their voice.

2. Script checkpoint. Do not render before this is approved.
   - Propose a beat table: time window, motion, on-screen text. See
     `references/script-checkpoint.md` for the template and the voice rules.
   - Keep text sparse: captions, axis labels, data annotations. Figures carry the argument.
   - Ask for the decisions that change the work: duration budget, sentence case vs lowercase,
     which evidence shows each result, whether a URL or logo belongs in the video, how many
     worked examples to show.
   - Distinct results get distinct scenes and captions. Never let one visual imply another
     result (for example, task-level variation versus a cost/performance frontier).
   - Any counter or label must match the granularity of what is drawn (15 cards are 15
     domains, not 90 tasks; say so on screen).

3. Build the renderer from `assets/render_template.py`.
   - Pillow frames at 2x supersampling downsampled with LANCZOS, encoded through
     imageio-ffmpeg (`uv run --no-project --with imageio-ffmpeg python render_video.py`).
     Matplotlib is fine for plots, but one drawing system keeps text consistent.
   - One `TEXT` dictionary holds every on-screen string. One timeline block holds every scene
     window. Scenes are functions of `t` that draw onto a transparent layer; the frame
     assembler crossfades layers.
   - Load the result tables and compute the shown quantities in code (win rates, frontier,
     medians). Write a `claim_problems()` function that returns every on-screen claim the
     tables do not support, and make the renderer refuse to run if it returns anything.
   - Ship fonts inside the package (Noto Sans under OFL is the usual choice) so the render is
     reproducible on another machine.
   - Show movement from the first frame. Make the final frame useful as a still; it is the
     poster.

4. Review frames before rendering the whole video.
   - Render one frame per beat with `--frame <seconds>` and look at them. Fix clipping,
     colliding labels, overflowing cells, illegible sizes (22 px is the floor at 1200 px on a
     phone). Also render mid-transition frames.
   - Then render everything, open the contact sheet, and check pacing: about 2 s per line a
     viewer must read, 5-8 s per data scene, at least 1.5 s of hold after the last element lands.
     Thirty seconds beats twenty for comprehension; ask before exceeding the budget.

5. Check, test, deliver.
   - Run `scripts/check_video.py` against the output directory. It parses the MP4 boxes
     directly (no ffprobe): dimensions, fps, duration, H.264, 4:2:0, fast-start, size, frame
     count, required claims, forbidden fragments, provenance hashes.
   - Add a unittest module that checks the committed MP4 contract, the text claims, the data
     claims, provenance drift, a few re-rendered key frames, and that the final frame equals the
     poster. Register loaded modules in `sys.modules` before `exec_module` or frozen dataclasses
     fail under `from __future__ import annotations`.
   - Write a README with the exact render and check commands, the export contract, a
     source-data table per scene, and the timeline.
   - Work on a branch, commit source and outputs together (tests hash-pin both), open a PR, and
     hand back the PR link plus the direct file link to the MP4. Do not merge unless asked.

## Voice rules (apply to every on-screen string)

- Technical guide, not trailer. No slogans, no "not x but y", no triadic drum rolls, no
  LinkedIn phrasing, no "unlock", "revolutionise", "game-changing", "delve".
- State scoped findings in the paper's or thread's own words ("Cost did not predict performance
  on the 11 shared tasks."), never a generalised version.
- Prefer a data annotation over a sentence ("GPT-5.4 nano: better at follow-up forecasting than
  phenotype recovery").
- Tag evidence boundaries on screen when the paper requires it ("validation split · 11 shared
  tasks").
- If the author rejects a line, do not reintroduce it in another form.

## Export contract (default)

1200 x 1200, 30 fps, H.264 High in MP4, `yuv420p`, `+faststart`, CRF 18, no audio, under 30 MB.
Duration per the user's budget; the contract checker takes the bounds from `provenance.json`.

## Deliverables

- `render_video.py` (source of truth), `check_video.py`, shipped fonts with licence.
- `outputs/<name>.mp4`, `outputs/poster.png`, `outputs/contact_sheet.png`, `outputs/provenance.json`.
- `README.md` in the package, a unittest module, a PR.

Read `references/pitfalls.md` before starting; it lists the failures that cost the most time.
