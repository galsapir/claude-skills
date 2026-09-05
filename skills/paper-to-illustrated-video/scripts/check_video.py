# ABOUTME: Verifies a rendered announcement video package against its export and claims contract.
# ABOUTME: Parses MP4 boxes directly (no ffprobe) and checks provenance.json for claims and hashes.

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_MIN_DURATION_S = 20.0
DEFAULT_MAX_DURATION_S = 35.0
DEFAULT_MAX_MB = 30.0
DEFAULT_FORBIDDEN: tuple[str, ...] = ("http", "www.", "participant_id")
HIGH_PROFILES = {100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135}


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration_s: float
    fps: float
    codec: str
    chroma_420: bool
    faststart: bool
    frame_count: int
    size_bytes: int


def iter_boxes(data: bytes, start: int, end: int) -> Iterator[tuple[str, int, int]]:
    """Yield (type, payload_start, box_end) for each ISO BMFF box in data[start:end]."""
    pos = start
    while pos + 8 <= end:
        size, kind = struct.unpack(">I4s", data[pos : pos + 8])
        header = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8 : pos + 16])[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header:
            raise ValueError(f"corrupt box at {pos}")
        yield kind.decode("latin1"), pos + header, pos + size
        pos += size


def child(data: bytes, start: int, end: int, kind: str) -> tuple[int, int]:
    for name, payload, box_end in iter_boxes(data, start, end):
        if name == kind:
            return payload, box_end
    raise KeyError(kind)


def video_trak(data: bytes, moov: tuple[int, int]) -> tuple[int, int]:
    for name, payload, box_end in iter_boxes(data, *moov):
        if name != "trak":
            continue
        mdia = child(data, payload, box_end, "mdia")
        hdlr = child(data, *mdia, "hdlr")
        if data[hdlr[0] + 8 : hdlr[0] + 12] == b"vide":
            return payload, box_end
    raise KeyError("video trak")


class BitReader:
    def __init__(self, payload: bytes) -> None:
        self.bits = "".join(f"{byte:08b}" for byte in payload)
        self.pos = 0

    def u(self, count: int) -> int:
        value = int(self.bits[self.pos : self.pos + count], 2) if count else 0
        self.pos += count
        return value

    def ue(self) -> int:
        zeros = 0
        while self.u(1) == 0:
            zeros += 1
        return (1 << zeros) - 1 + self.u(zeros)


def strip_emulation_prevention(nal: bytes) -> bytes:
    out = bytearray()
    zeros = 0
    for byte in nal:
        if zeros >= 2 and byte == 3:
            zeros = 0
            continue
        out.append(byte)
        zeros = zeros + 1 if byte == 0 else 0
    return bytes(out)


def sps_is_420(sps: bytes) -> bool:
    """Decode chroma_format_idc from an H.264 SPS; profiles without it default to 4:2:0."""
    reader = BitReader(strip_emulation_prevention(sps[1:]))
    profile_idc = reader.u(8)
    reader.u(8)  # constraint flags
    reader.u(8)  # level_idc
    reader.ue()  # seq_parameter_set_id
    if profile_idc not in HIGH_PROFILES:
        return True
    return reader.ue() == 1


def probe(path: Path) -> VideoInfo:
    """Read container and codec facts straight from the MP4 boxes."""
    data = path.read_bytes()
    top = list(iter_boxes(data, 0, len(data)))
    order = [name for name, _p, _e in top]
    if "moov" not in order or "mdat" not in order:
        raise ValueError("not a complete MP4: missing moov or mdat")
    faststart = order.index("moov") < order.index("mdat")
    moov = next((p, e) for name, p, e in top if name == "moov")

    mvhd = child(data, *moov, "mvhd")
    if data[mvhd[0]] == 1:
        timescale = struct.unpack(">I", data[mvhd[0] + 20 : mvhd[0] + 24])[0]
        duration = struct.unpack(">Q", data[mvhd[0] + 24 : mvhd[0] + 32])[0]
    else:
        timescale, duration = struct.unpack(">II", data[mvhd[0] + 12 : mvhd[0] + 20])

    trak = video_trak(data, moov)
    tkhd = child(data, *trak, "tkhd")
    offset = tkhd[0] + (88 if data[tkhd[0]] == 1 else 76)
    width_fixed, height_fixed = struct.unpack(">II", data[offset : offset + 8])

    mdia = child(data, *trak, "mdia")
    mdhd = child(data, *mdia, "mdhd")
    if data[mdhd[0]] == 1:
        media_timescale = struct.unpack(">I", data[mdhd[0] + 20 : mdhd[0] + 24])[0]
    else:
        media_timescale = struct.unpack(">I", data[mdhd[0] + 12 : mdhd[0] + 16])[0]
    stbl = child(data, *child(data, *mdia, "minf"), "stbl")

    stsd = child(data, *stbl, "stsd")
    entry_start = stsd[0] + 8
    entry_size, entry_format = struct.unpack(">I4s", data[entry_start : entry_start + 8])
    codec = entry_format.decode("latin1")
    chroma_420 = False
    if codec == "avc1":
        avcc = child(data, entry_start + 8 + 78, entry_start + entry_size, "avcC")
        sps_count = data[avcc[0] + 5] & 0x1F
        pos = avcc[0] + 6
        for _ in range(sps_count):
            length = struct.unpack(">H", data[pos : pos + 2])[0]
            chroma_420 = sps_is_420(data[pos + 2 : pos + 2 + length])
            pos += 2 + length

    stts = child(data, *stbl, "stts")
    entry_count = struct.unpack(">I", data[stts[0] + 4 : stts[0] + 8])[0]
    frame_count = 0
    deltas: set[int] = set()
    for index in range(entry_count):
        count, delta = struct.unpack(">II", data[stts[0] + 8 + index * 8 : stts[0] + 16 + index * 8])
        frame_count += count
        deltas.add(delta)
    fps = media_timescale / max(deltas) if deltas else 0.0

    return VideoInfo(
        width=width_fixed >> 16,
        height=height_fixed >> 16,
        duration_s=duration / timescale,
        fps=fps,
        codec=codec,
        chroma_420=chroma_420,
        faststart=faststart,
        frame_count=frame_count,
        size_bytes=len(data),
    )


def check_video(
    path: Path,
    *,
    size: int,
    fps: int,
    expected_frames: int | None,
    min_duration_s: float = DEFAULT_MIN_DURATION_S,
    max_duration_s: float = DEFAULT_MAX_DURATION_S,
    max_mb: float = DEFAULT_MAX_MB,
) -> list[str]:
    """Return every violation of the export contract for one MP4."""
    if not path.is_file():
        return [f"missing video {path}"]
    info = probe(path)
    problems: list[str] = []
    if (info.width, info.height) != (size, size):
        problems.append(f"dimensions {info.width}x{info.height}, expected {size}x{size}")
    if abs(info.fps - fps) > 0.01:
        problems.append(f"fps {info.fps:.3f}, expected {fps}")
    if not min_duration_s <= info.duration_s <= max_duration_s:
        problems.append(f"duration {info.duration_s:.2f}s outside {min_duration_s}-{max_duration_s}s")
    if info.codec != "avc1":
        problems.append(f"codec {info.codec}, expected avc1 (H.264)")
    if not info.chroma_420:
        problems.append("pixel format is not 4:2:0 (yuv420p)")
    if not info.faststart:
        problems.append("moov box is after mdat; not fast-start")
    if info.size_bytes >= max_mb * 1024 * 1024:
        problems.append(f"file size {info.size_bytes / 1e6:.1f} MB exceeds {max_mb:g} MB")
    if expected_frames is not None and info.frame_count != expected_frames:
        problems.append(f"frame count {info.frame_count}, expected {expected_frames}")
    return problems


def check_claims(
    text: dict[str, str],
    required: list[str],
    forbidden: list[str] | tuple[str, ...] = DEFAULT_FORBIDDEN,
) -> list[str]:
    """Return every required claim missing from, or forbidden fragment present in, the on-screen text."""
    joined = "\n".join(text.values())
    problems = [f"required claim missing from on-screen text: {claim!r}" for claim in required if claim not in joined]
    lowered = joined.lower()
    problems += [f"forbidden fragment in on-screen text: {frag!r}" for frag in forbidden if frag.lower() in lowered]
    return problems


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_provenance(record: dict[str, object], root: Path) -> list[str]:
    """Return every input or output whose bytes no longer match the recorded hash."""
    problems: list[str] = []
    for group in ("inputs", "outputs"):
        for item in record.get(group, []):  # type: ignore[union-attr]
            path = root / str(item["path"])
            if not path.is_file():
                problems.append(f"{group}: missing {item['path']}")
            elif sha256_file(path) != item["sha256"]:
                problems.append(f"{group}: hash drift in {item['path']}")
    return problems


def check_package(out_dir: Path, root: Path) -> list[str]:
    """Run every check for a rendered video package directory.

    provenance.json is expected to carry: render {size, fps, frames, video_name}, contract
    {min_duration_s, max_duration_s, max_mb}, text, required_claims, optional forbidden_fragments,
    inputs and outputs with sha256.
    """
    record_path = out_dir / "provenance.json"
    if not record_path.is_file():
        return [f"missing {record_path}"]
    record = json.loads(record_path.read_text())
    render = record["render"]
    contract = record.get("contract", {})
    problems = check_video(
        out_dir / str(render.get("video_name", "video.mp4")),
        size=int(render["size"]),
        fps=int(render["fps"]),
        expected_frames=int(render["frames"]),
        min_duration_s=float(contract.get("min_duration_s", DEFAULT_MIN_DURATION_S)),
        max_duration_s=float(contract.get("max_duration_s", DEFAULT_MAX_DURATION_S)),
        max_mb=float(contract.get("max_mb", DEFAULT_MAX_MB)),
    )
    problems += check_claims(
        record["text"],
        list(record.get("required_claims", [])),
        tuple(record.get("forbidden_fragments", DEFAULT_FORBIDDEN)),
    )
    problems += check_provenance(record, root)
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a rendered announcement video package.")
    parser.add_argument("out_dir", type=Path, help="directory holding the MP4 and provenance.json")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root that provenance paths are relative to")
    args = parser.parse_args()
    record = json.loads((args.out_dir / "provenance.json").read_text())
    info = probe(args.out_dir / str(record["render"].get("video_name", "video.mp4")))
    print(json.dumps(info.__dict__, indent=2))
    problems = check_package(args.out_dir, args.root)
    for problem in problems:
        print("FAIL:", problem)
    if problems:
        sys.exit(1)
    print("OK: all checks passed")


if __name__ == "__main__":
    main()
