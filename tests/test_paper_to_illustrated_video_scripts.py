# ABOUTME: Tests the scripts bundled with the paper-to-illustrated-video skill.
# ABOUTME: Covers MP4 box parsing, SPS chroma decoding, claim checks, and provenance drift without ffmpeg.

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "paper-to-illustrated-video"


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", 8 + len(payload), kind) + payload


def bits(pattern: str) -> bytes:
    padded = pattern + "0" * (-len(pattern) % 8)
    return int(padded, 2).to_bytes(len(padded) // 8, "big")


class CheckVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_script("check_video")

    def test_iter_boxes_reports_top_level_order(self) -> None:
        data = box(b"ftyp", b"isom") + box(b"moov", b"") + box(b"mdat", b"\x00" * 4)
        names = [name for name, _p, _e in self.check.iter_boxes(data, 0, len(data))]
        self.assertEqual(names, ["ftyp", "moov", "mdat"])

    def test_sps_high_profile_reads_chroma_format_idc(self) -> None:
        # nal header, profile_idc=100, constraints, level, sps_id ue(0)="1", chroma_format_idc ue(1)="010"
        sps = b"\x67" + bits("01100100" + "00000000" + "00011111" + "1" + "010")
        self.assertTrue(self.check.sps_is_420(sps))
        sps_444 = b"\x67" + bits("01100100" + "00000000" + "00011111" + "1" + "00100")
        self.assertFalse(self.check.sps_is_420(sps_444))

    def test_sps_main_profile_is_420_by_definition(self) -> None:
        sps = b"\x67" + bits("01001101" + "00000000" + "00011111" + "1")
        self.assertTrue(self.check.sps_is_420(sps))

    def test_strip_emulation_prevention_removes_marker_byte(self) -> None:
        self.assertEqual(self.check.strip_emulation_prevention(b"\x00\x00\x03\x01"), b"\x00\x00\x01")

    def test_check_claims_flags_missing_required_and_forbidden_fragments(self) -> None:
        text = {"a": "Cost did not predict performance.", "b": "see https://example.org"}
        problems = self.check.check_claims(text, ["Cost did not predict performance", "validation split"])
        self.assertEqual(len(problems), 2)
        self.assertTrue(any("validation split" in p for p in problems))
        self.assertTrue(any("http" in p for p in problems))

    def test_check_provenance_detects_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "table.csv").write_text("a,b\n1,2\n")
            good = hashlib.sha256((root / "table.csv").read_bytes()).hexdigest()
            record = {"inputs": [{"path": "table.csv", "sha256": good}], "outputs": []}
            self.assertEqual(self.check.check_provenance(record, root), [])
            (root / "table.csv").write_text("a,b\n1,3\n")
            self.assertEqual(len(self.check.check_provenance(record, root)), 1)

    def test_check_package_reports_missing_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory)
            record = {
                "render": {"size": 1200, "fps": 30, "frames": 900, "video_name": "x.mp4"},
                "text": {"t": "PhenoBench"},
                "required_claims": ["PhenoBench"],
                "inputs": [],
                "outputs": [],
            }
            (out_dir / "provenance.json").write_text(json.dumps(record))
            problems = self.check.check_package(out_dir, out_dir)
            self.assertEqual(len(problems), 1)
            self.assertIn("missing video", problems[0])


class RenderTemplateTests(unittest.TestCase):
    def test_template_renders_a_frame_without_shipped_fonts(self) -> None:
        spec = importlib.util.spec_from_file_location("render_template", SKILL / "assets" / "render_template.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["render_template"] = module
        spec.loader.exec_module(module)
        frame = module.frame_at(1.0, module.load_data())
        self.assertEqual(frame.size, (module.SIZE, module.SIZE))
        self.assertEqual(module.claim_problems(module.load_data()), [])
        self.assertIn("takeaway", module.TEXT)


if __name__ == "__main__":
    unittest.main()
