# ABOUTME: Starting point for a deterministic announcement-video renderer (Pillow frames, ffmpeg encode).
# ABOUTME: Copy into the paper repository, fill TEXT, the timeline, the scenes, and claim_problems().

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]  # adjust to the repository root
PACKAGE = Path(__file__).resolve().parent
OUTPUT_DIR = PACKAGE / "outputs"
FONT_DIR = PACKAGE / "assets" / "fonts"  # ship NotoSans-Regular.ttf, NotoSans-Bold.ttf, OFL.txt here

INPUTS: tuple[Path, ...] = ()  # aggregate tables and figure files the video is built from

VIDEO_NAME = "announcement.mp4"
POSTER_NAME = "poster.png"
CONTACT_SHEET_NAME = "contact_sheet.png"
PROVENANCE_NAME = "provenance.json"

SIZE = 1200
SS = 2
FPS = 30
DURATION_S = 30.0
N_FRAMES = int(round(DURATION_S * FPS))
CONTRACT = {"min_duration_s": 20.0, "max_duration_s": 35.0, "max_mb": 30.0}
CONTACT_TIMES: tuple[float, ...] = tuple(round(DURATION_S * k / 11, 1) for k in range(12))

PAPER = "#FBFCFE"
WHITE = "#FFFFFF"
NAVY = "#17324D"
SLATE = "#60717F"
GRID = "#DCE5EA"
TEAL = "#109D83"

# Every on-screen string lives here so tests and provenance can see all of them.
TEXT: dict[str, str] = {
    "opening_wordmark": "Paper name",
    "opening_sub": "illustrated",
    "scene_eyebrow": "Result",
    "scene_title": "What the figure shows",
    "scene_sub": "n models · n tasks · evidence split",
    "takeaway": "The paper's own sentence for the finding.",
    "wordmark": "Paper name",
}
REQUIRED_CLAIMS: tuple[str, ...] = ("The paper's own sentence",)

# Timeline in seconds. Neighbouring scenes overlap by the crossfade.
T_OPENING = (0.0, 2.2)
T_SCENE = (1.9, DURATION_S)
T_TAKEAWAY = (DURATION_S - 1.8, DURATION_S - 1.2)
T_WORDMARK = (DURATION_S - 1.2, DURATION_S - 0.6)


def ease(t: float, t0: float, t1: float) -> float:
    """Smoothstep progress of t across [t0, t1], clamped to [0, 1]."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
    return u * u * (3.0 - 2.0 * u)


def hex_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load the shipped font at the supersampled size; fall back to Pillow's default face."""
    key = ("bold" if bold else "regular", size)
    if key not in _FONT_CACHE:
        path = FONT_DIR / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")
        if path.is_file():
            _FONT_CACHE[key] = ImageFont.truetype(str(path), size * SS)
        else:
            _FONT_CACHE[key] = ImageFont.load_default(size * SS)
    return _FONT_CACHE[key]


def wrap(text: str, text_font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: float) -> list[str]:
    """Greedy word wrap using measured pixel widths in canvas units."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and text_font.getlength(candidate) / SS > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


class Sheet:
    """Supersampled RGBA drawing surface addressed in canvas units (SIZE x SIZE)."""

    def __init__(self, background: str | None = None) -> None:
        color = (*hex_rgb(background), 255) if background else (0, 0, 0, 0)
        self.image = Image.new("RGBA", (SIZE * SS, SIZE * SS), color)
        self.draw = ImageDraw.Draw(self.image)

    @staticmethod
    def _s(value: float) -> int:
        return int(round(value * SS))

    def _box(self, box: Sequence[float]) -> tuple[int, int, int, int]:
        return self._s(box[0]), self._s(box[1]), self._s(box[2]), self._s(box[3])

    def rrect(self, box: Sequence[float], radius: float, fill=None, outline=None, width: float = 0) -> None:
        self.draw.rounded_rectangle(self._box(box), radius=self._s(radius), fill=fill, outline=outline,
                                    width=self._s(width))

    def rect(self, box: Sequence[float], fill=None) -> None:
        self.draw.rectangle(self._box(box), fill=fill)

    def line(self, points: Sequence[tuple[float, float]], fill, width: float) -> None:
        self.draw.line([(self._s(x), self._s(y)) for x, y in points], fill=fill,
                       width=max(1, self._s(width)), joint="curve")

    def circle(self, center: tuple[float, float], radius: float, fill, outline=None, width: float = 0) -> None:
        x, y = center
        self.draw.ellipse(self._box((x - radius, y - radius, x + radius, y + radius)), fill=fill,
                          outline=outline, width=self._s(width))

    def text(self, xy: tuple[float, float], text: str, text_font, fill, anchor: str = "la") -> None:
        self.draw.text((self._s(xy[0]), self._s(xy[1])), text, font=text_font, fill=fill, anchor=anchor)

    def text_block(self, xy: tuple[float, float], lines: Sequence[str], text_font, fill, line_height: float,
                   anchor: str = "la") -> float:
        x, y = xy
        for line in lines:
            self.text((x, y), line, text_font, fill, anchor)
            y += line_height
        return y

    def paste(self, image: Image.Image, xy: tuple[float, float], alpha: float = 1.0) -> None:
        """Alpha-composite an RGBA image whose pixel size is already supersampled."""
        if alpha <= 0:
            return
        layer = image
        if alpha < 1.0:
            layer = image.copy()
            layer.putalpha(image.getchannel("A").point(lambda v: int(v * alpha)))
        self.image.alpha_composite(layer, (self._s(xy[0]), self._s(xy[1])))

    def composite(self, other: "Sheet", alpha: float = 1.0) -> None:
        if alpha <= 0:
            return
        layer = other.image
        if alpha < 1.0:
            layer = other.image.copy()
            layer.putalpha(other.image.getchannel("A").point(lambda v: int(v * alpha)))
        self.image.alpha_composite(layer)

    def finish(self) -> Image.Image:
        return self.image.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)


# ----------------------------------------------------------------------------------------------
# Data and claims. Load the aggregate tables here and derive every number that appears on screen.
# ----------------------------------------------------------------------------------------------


def load_data() -> dict[str, object]:
    return {}


def claim_problems(data: dict[str, object]) -> list[str]:
    """Return every on-screen claim that the source tables do not support. Empty means render."""
    return []


# ----------------------------------------------------------------------------------------------
# Scenes. Each draws onto a transparent layer for time t; the assembler crossfades layers.
# ----------------------------------------------------------------------------------------------


def draw_header(sheet: Sheet, eyebrow: str, title: str, sub: str, alpha: float) -> None:
    if alpha <= 0:
        return
    layer = Sheet()
    layer.rect((60, 58, 68, 118), fill=TEAL)
    layer.text((88, 66), eyebrow.upper(), font(21, bold=True), TEAL)
    layer.text((88, 97), title, font(38, bold=True), NAVY)
    layer.text((88, 152), sub, font(22), SLATE)
    sheet.composite(layer, alpha)


def scene_opening(sheet: Sheet, t: float) -> None:
    out = 1 - ease(t, T_OPENING[1] - 0.5, T_OPENING[1])
    mark = ease(t, 0.15, 0.85) * out
    if mark > 0:
        layer = Sheet()
        layer.text((SIZE / 2, SIZE / 2 - 30), TEXT["opening_wordmark"], font(92, bold=True), NAVY, anchor="mm")
        sheet.composite(layer, mark)
    sub = ease(t, 0.55, 1.15) * out
    if sub > 0:
        layer = Sheet()
        layer.text((SIZE / 2, SIZE / 2 + 52), TEXT["opening_sub"], font(34), SLATE, anchor="mm")
        sheet.composite(layer, sub)


def scene_result(sheet: Sheet, t: float, data: dict[str, object]) -> None:
    start = T_SCENE[0]
    header_alpha = ease(t, start + 0.3, start + 0.8) * (1 - ease(t, *T_TAKEAWAY))
    draw_header(sheet, TEXT["scene_eyebrow"], TEXT["scene_title"], TEXT["scene_sub"], header_alpha)
    # Draw the figure here: axes grow, points appear in a meaningful order, intervals extend,
    # then the derived line or highlight. Keep each element's timing relative to `start`.
    plot = Sheet()
    spine = ease(t, start + 0.4, start + 1.1)
    if spine > 0:
        plot.line([(200, 940), (200, 940 - 670 * spine)], NAVY, 2)
        plot.line([(200, 940), (200 + 910 * spine, 940)], NAVY, 2)
    sheet.composite(plot, 1 - 0.22 * ease(t, *T_TAKEAWAY))

    takeaway_alpha = ease(t, *T_TAKEAWAY)
    if takeaway_alpha > 0:
        layer = Sheet()
        take_font = font(36, bold=True)
        lines = wrap(TEXT["takeaway"], take_font, 1060)
        layer.rect((60, 66, 68, 66 + len(lines) * 50 - 6), fill=TEAL)
        layer.text_block((88, 90), lines, take_font, NAVY, 50, anchor="lm")
        sheet.composite(layer, takeaway_alpha)
    wordmark_alpha = ease(t, *T_WORDMARK)
    if wordmark_alpha > 0:
        layer = Sheet()
        layer.text((SIZE / 2, 1090), TEXT["wordmark"], font(60, bold=True), NAVY, anchor="mm")
        sheet.composite(layer, wordmark_alpha)


# ----------------------------------------------------------------------------------------------
# Frame assembly and outputs
# ----------------------------------------------------------------------------------------------


def window_alpha(t: float, start: float, end: float, fade: float = 0.45) -> float:
    if t < start or t > end:
        return 0.0
    return min(ease(t, start, start + fade), 1 - ease(t, end - fade, end))


def frame_at(t: float, data: dict[str, object]) -> Image.Image:
    """Render the finished SIZE x SIZE RGB frame at time t seconds."""
    sheet = Sheet(PAPER)
    if T_OPENING[0] <= t <= T_OPENING[1]:
        layer = Sheet()
        scene_opening(layer, t)
        sheet.composite(layer, 1.0)
    if t >= T_SCENE[0]:
        layer = Sheet()
        scene_result(layer, t, data)
        sheet.composite(layer, ease(t, T_SCENE[0], T_SCENE[0] + 0.45))
    return sheet.finish()


def frame_time(index: int) -> float:
    return index / FPS


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode_video(data: dict[str, object], out_path: Path,
                 on_frame: Callable[[int, Image.Image], None] | None = None) -> None:
    import imageio_ffmpeg

    writer = imageio_ffmpeg.write_frames(
        str(out_path), (SIZE, SIZE), fps=FPS, codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
        macro_block_size=8,
        output_params=["-crf", "18", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
                       "-movflags", "+faststart", "-g", "60"],
    )
    writer.send(None)
    try:
        for index in range(N_FRAMES):
            frame = frame_at(frame_time(index), data)
            if on_frame is not None:
                on_frame(index, frame)
            writer.send(np.asarray(frame, dtype=np.uint8).tobytes())
    finally:
        writer.close()


def contact_sheet(frames: Sequence[tuple[float, Image.Image]]) -> Image.Image:
    columns, thumb, pad, caption = 4, 380, 16, 34
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new("RGB", (columns * thumb + (columns + 1) * pad, rows * (thumb + caption) + (rows + 1) * pad), WHITE)
    draw = ImageDraw.Draw(sheet)
    label_font = font(20)
    for index, (t, frame) in enumerate(frames):
        row, column = divmod(index, columns)
        x = pad + column * (thumb + pad)
        y = pad + row * (thumb + caption + pad)
        sheet.paste(frame.resize((thumb, thumb), Image.LANCZOS), (x, y))
        draw.rectangle((x, y, x + thumb - 1, y + thumb - 1), outline=GRID)
        draw.text((x, y + thumb + 6), f"t = {t:.1f} s", font=label_font, fill=NAVY)
    return sheet


def provenance(data: dict[str, object], out_dir: Path) -> dict[str, object]:
    return {
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256_file(p)} for p in INPUTS],
        "render": {"size": SIZE, "fps": FPS, "duration_s": DURATION_S, "frames": N_FRAMES, "supersample": SS,
                   "video_name": VIDEO_NAME},
        "contract": CONTRACT,
        "text": TEXT,
        "required_claims": list(REQUIRED_CLAIMS),
        "derived": {},  # numbers computed from the tables that appear on screen
        "outputs": [
            {"path": str((out_dir / name).relative_to(ROOT)), "sha256": sha256_file(out_dir / name)}
            for name in (VIDEO_NAME, POSTER_NAME, CONTACT_SHEET_NAME)
        ],
    }


def render_all(out_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Render the video, poster, contact sheet and provenance record into out_dir."""
    data = load_data()
    problems = claim_problems(data)
    if problems:
        raise SystemExit("on-screen claims are not supported by the source tables:\n  " + "\n  ".join(problems))
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = {int(round(t * FPS)): t for t in CONTACT_TIMES}
    captured: dict[int, Image.Image] = {}
    last: dict[str, Image.Image] = {}

    def keep(index: int, frame: Image.Image) -> None:
        if index in wanted:
            captured[index] = frame
        if index == N_FRAMES - 1:
            last["frame"] = frame

    encode_video(data, out_dir / VIDEO_NAME, keep)
    last["frame"].save(out_dir / POSTER_NAME, optimize=True)
    contact_sheet([(wanted[i], captured[i]) for i in sorted(captured)]).save(out_dir / CONTACT_SHEET_NAME, optimize=True)
    (out_dir / PROVENANCE_NAME).write_text(json.dumps(provenance(data, out_dir), indent=2) + "\n")
    return [out_dir / name for name in (VIDEO_NAME, POSTER_NAME, CONTACT_SHEET_NAME, PROVENANCE_NAME)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the announcement video.")
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--frame", type=float, action="append", default=[],
                        help="render one frame at this time (seconds) to out-dir as frame_<t>.png")
    args = parser.parse_args()
    if args.frame:
        data = load_data()
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for t in args.frame:
            frame_at(t, data).save(args.out_dir / f"frame_{t:05.2f}.png")
        return
    for path in render_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
