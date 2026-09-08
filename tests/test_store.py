from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
STORE = REPO / ".agents" / "skills" / "ai-learning-sensei" / "scripts" / "sensei_store.py"
COLLECT = REPO / ".agents" / "skills" / "ai-learning-sensei" / "scripts" / "collect_sources.py"


class SenseiStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        (self.root / "inbox").mkdir()
        profile = {
            "learner": {"role": "Product manager", "timezone": "UTC", "language": "en"},
            "learning_goals": ["Build reliable AI agents"],
            "real_work_tasks": ["Automate customer research"],
            "priority_areas": ["agent evaluation"],
            "low_priority_areas": ["video generation"],
            "cadence": {"sessions_per_week": 2, "session_minutes": 45},
            "backlog_file": "BACKLOG.md",
        }
        sources = {"collection": {"lookback_days": 30}, "sources": []}
        (self.root / "config" / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
        (self.root / "config" / "sources.json").write_text(json.dumps(sources), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_store(self, *args: str) -> object:
        result = subprocess.run(
            [sys.executable, str(STORE), "--repo-root", str(self.root), *args],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        return json.loads(result.stdout)

    def test_full_session_lifecycle_and_ai_gate(self) -> None:
        self.assertTrue(self.run_store("validate-config")["valid"])
        self.run_store("init")
        self.run_store("ingest", "--title", "Evaluate an AI agent", "--text", "Build an LLM eval workflow")
        self.run_store("ingest", "--title", "Traditional gardening", "--text", "Plant tomatoes outdoors")
        self.run_store("maintain")
        status = self.run_store("status")
        self.assertEqual(status["counts"]["active_materials"], 1)
        self.assertEqual(status["counts"]["rejected_materials"], 1)
        self.assertIn("Evaluate an AI agent", (self.root / "BACKLOG.md").read_text(encoding="utf-8"))

        session = self.run_store("record-choice", "--topic", "Evaluate an AI agent", "--materials", "1")
        retrospective = self.root / "retrospectives" / "2026-01-01-agent-eval.md"
        retrospective.parent.mkdir()
        retrospective.write_text("# Retrospective", encoding="utf-8")
        self.run_store(
            "complete", "--session-id", str(session["session_id"]),
            "--usefulness", "5", "--difficulty", "3",
            "--artifact", "eval.md", "--retrospective", str(retrospective),
        )
        backlog = (self.root / "BACKLOG.md").read_text(encoding="utf-8")
        self.assertIn("S1", backlog)
        self.assertIn("5 / 3", backlog)

    def test_local_file_collection(self) -> None:
        (self.root / "inbox" / "learning.md").write_text(
            "Build a Claude AI agent and test it with an evaluation dataset.", encoding="utf-8"
        )
        sources = {
            "collection": {"lookback_days": 30},
            "sources": [{"name": "My inbox", "type": "file", "path": "inbox/learning.md", "enabled": True}],
        }
        (self.root / "config" / "sources.json").write_text(json.dumps(sources), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(COLLECT), "--repo-root", str(self.root)],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["sources"][0]["added"], 1)
        self.run_store("maintain")
        self.assertEqual(self.run_store("status")["counts"]["active_materials"], 1)

    def test_public_social_source_needs_no_ownership_and_export_needs_authorization(self) -> None:
        (self.root / "inbox" / "social.md").write_text(
            "My post about testing an LLM agent with evals.", encoding="utf-8"
        )
        public_source = {
            "collection": {},
            "sources": [{
                "name": "Public AI page", "type": "social", "platform": "instagram",
                "url": "https://example.com/public-ai-page", "collection_method": "public_web",
                "enabled": False,
            }],
        }
        config_path = self.root / "config" / "sources.json"
        config_path.write_text(json.dumps(public_source), encoding="utf-8")
        self.assertTrue(self.run_store("validate-config")["valid"])

        unauthorized_export = {
            "collection": {},
            "sources": [{
                "name": "Social export", "type": "social", "platform": "instagram",
                "path": "inbox/social.md", "collection_method": "export_file",
                "access_authorized": False, "enabled": True,
            }],
        }
        config_path.write_text(json.dumps(unauthorized_export), encoding="utf-8")
        invalid = subprocess.run(
            [sys.executable, str(STORE), "--repo-root", str(self.root), "validate-config"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("access_authorized", invalid.stderr)

        unauthorized_export["sources"][0]["access_authorized"] = True
        config_path.write_text(json.dumps(unauthorized_export), encoding="utf-8")
        self.assertTrue(self.run_store("validate-config")["valid"])
        result = subprocess.run(
            [sys.executable, str(COLLECT), "--repo-root", str(self.root)],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(json.loads(result.stdout)["sources"][0]["added"], 1)


if __name__ == "__main__":
    unittest.main()
