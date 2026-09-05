# Pitfalls

Each of these cost real time on a previous video. Check them before you hit them.

## Source figures

- An AI-generated figure panel is usually one embedded raster, even inside a PDF. Nothing in it
  is a vector element. Body silhouettes, icons and cards are pixel crops; text must be redrawn.
- Read the raster from the committed PNG rather than extracting it from the PDF; that removes a
  pymupdf dependency from tests. Express crop boxes in the raster's native pixel grid and scale
  them by `png.width / native_width`.
- Removing leader lines and arrows around a silhouette by colour fails: the body fill is within a
  few levels of the page background and the raster is noisy. What worked: threshold dark strokes,
  close small gaps, `binary_fill_holes` on the closed outline, drop strokes, label the enclosed
  regions, keep the largest region plus any region whose median shade is below background and
  that touches the body (limbs cut off by a crossing line, organs), then fill holes and dilate a
  few pixels to recover the outline. Arrowheads that overlap the silhouette stay; they are part
  of the source drawing.
- Tint near-white fill inside the silhouette slightly so the body reads against the page
  background. Do not boost contrast globally; it amplifies raster noise.

## Drawing

- Pillow's `ImageDraw` is not anti-aliased. Draw at 2x and downsample with LANCZOS.
- Ship the fonts (Noto Sans Regular and Bold, OFL) inside the package. System variable fonts
  behave differently across Pillow and Matplotlib.
- Wrap text by measured pixel width, not character count, and check every cell for overflow at
  the longest value. Long values overflow silently.
- Column headers in a heatmap collide when cells are narrower than the longest header. Widen the
  cells or shrink the header font before touching the labels.
- Labels next to scatter points collide with other points' confidence intervals. Place labels
  per point with explicit offsets and anchors; check the frame.
- A colour-only heatmap needs a legend. Numbers on the leader row and the called-out rows are
  enough for comprehension.

## Timeline

- Show motion from frame zero, but a fade-in makes early frames low-variance. Do not test
  "frame is not blank" at 0.5 s of a fade; test at 1 s or later and test motion separately by
  comparing frame 0.0 and 0.3.
- Connector or accent animations that start before their parent element is visible look like
  glitches. Start them after the parent's pop finishes.
- Slower is better. Twenty seconds felt rushed to the author; thirty-one seconds landed.

## Encoding and checks

- `imageio-ffmpeg` is installed per invocation with `uv run --no-project --with imageio-ffmpeg`.
  It bundles a static ffmpeg; no system ffmpeg is needed, and there is no ffprobe. Parse the MP4
  boxes yourself (see `scripts/check_video.py`).
- `-movflags +faststart` puts `moov` before `mdat`; check the top-level box order.
- `yuv420p` is confirmed from the SPS `chroma_format_idc` in `avcC`, after stripping emulation
  prevention bytes. Profiles without that field are 4:2:0 by definition.
- Output params that worked: `-crf 18 -preset slow -profile:v high -level 4.0 -g 60`.
  Thirty-one seconds of mostly static frames at 1200x1200 is about 2 MB.

## Tests

- Loading a module by path with `importlib.util` must register it in `sys.modules` before
  `exec_module`, or frozen dataclasses raise `AttributeError: 'NoneType' object has no attribute
  '__dict__'` under `from __future__ import annotations`.
- Hash-pin inputs and outputs in `provenance.json` and assert no drift. Commit source, outputs and
  provenance in the same commit.
- Assert that the rendered final frame equals the committed poster (mean absolute difference
  below 1.0). It catches any silent change to the last scene.

## Process

- Ask before drafting text in the author's voice; read two recent posts of theirs first.
- Confirm task cards or registry entries for any example task you show; wording and metrics come
  from those, not from memory. Flag "draft" status to the author.
- Record the author's decisions (duration, case, URL, examples) in memory so the next revision
  does not re-ask them.
