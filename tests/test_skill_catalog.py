# ABOUTME: Tests repository-level skill catalog expectations.
# ABOUTME: Covers install metadata and core skill contract text.
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter_value(content: str, key: str) -> str:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match is None:
        raise AssertionError("missing YAML frontmatter")

    field = re.search(rf"^{re.escape(key)}:\s*(.+)$", match.group(1), re.MULTILINE)
    if field is None:
        raise AssertionError(f"missing frontmatter key: {key}")
    return field.group(1).strip()


class SkillCatalogTests(unittest.TestCase):
    def test_long_horizon_skill_is_catalogued_for_npx_install(self) -> None:
        readme = read_text(ROOT / "README.md")
        skill = ROOT / "skills" / "long-horizon" / "SKILL.md"

        self.assertTrue(skill.exists())
        self.assertIn("npx skills add galsapir/skills --skill long-horizon", readme)
        self.assertIn("### `long-horizon`", readme)

    def test_long_horizon_skill_has_installable_metadata(self) -> None:
        skill_dir = ROOT / "skills" / "long-horizon"
        skill = read_text(skill_dir / "SKILL.md")
        openai_yaml = read_text(skill_dir / "agents" / "openai.yaml")

        self.assertEqual(frontmatter_value(skill, "name"), "long-horizon")
        self.assertIn("description:", skill)
        self.assertIn('display_name: "Long Horizon"', openai_yaml)
        self.assertIn("$long-horizon", openai_yaml)

    def test_long_horizon_skill_contains_prompt_wrapper_contract(self) -> None:
        skill = read_text(ROOT / "skills" / "long-horizon" / "SKILL.md")

        self.assertIn("Take the user's draft prompt as-is", skill)
        self.assertIn("Do not paraphrase", skill)
        self.assertIn("implementation-notes.html", skill)
        self.assertIn("Design decisions", skill)
        self.assertIn("Deviations", skill)
        self.assertIn("Tradeoffs", skill)
        self.assertIn("Open questions", skill)
        self.assertIn("subagents", skill)


if __name__ == "__main__":
    unittest.main()
