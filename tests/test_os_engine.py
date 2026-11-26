"""Checks for the Helix-Matrix day engine.

Run: python3 -m pytest tests -q     (from the repository root)
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

import os_engine as eng  # noqa: E402

READMES = ROOT
REMOTE = eng.resolve_projects(ROOT)
# When the app is checked out without the owner's project clones (e.g. on a CI
# runner), the engine still works — project-dependent facts are skipped there.
HAS_PROJECTS = REMOTE.is_dir()
DAY = date(2026, 11, 19)
# Public Egyptian Survey table for Cairo on this date (Aladhan method 5).
ALADHAN = {
    "fajr": "04:53",
    "sunrise": "06:23",
    "dhuhr": "11:40",
    "asr": "14:38",
    "maghrib": "16:57",
    "isha": "18:18",
}


def minutes(clock: str) -> int:
    hour, minute = clock.split(":")
    return int(hour) * 60 + int(minute)


class PrayerTests(unittest.TestCase):
    def test_cairo_19_nov_2026_within_one_minute(self):
        got = eng.prayer_times(DAY)
        for name, expected in ALADHAN.items():
            self.assertLessEqual(abs(minutes(got[name]) - minutes(expected)), 1, name)

    def test_windows_follow_prayer_order(self):
        prayers = eng.prayer_times(DAY)
        windows = eng.windows_for(prayers)
        self.assertEqual([row["id"] for row in windows], [row[0] for row in eng.WINDOWS])
        self.assertEqual(eng.current_window(prayers, "12:00"), "dhuhr_asr")
        self.assertIsNone(eng.current_window(prayers, "03:00"))


class SourceTests(unittest.TestCase):
    def test_real_folders(self):
        sources = eng.read_sources(READMES, REMOTE)
        self.assertGreaterEqual(len(sources["terms"]), 10)
        self.assertEqual(len(sources["lessons"]), 24)
        if not HAS_PROJECTS:
            self.assertEqual(len(sources["projects"]), 0)
            return
        self.assertGreaterEqual(len(sources["projects"]), 10)
        recorded = [lesson for lesson in sources["lessons"] if lesson["recorded"]]
        self.assertTrue(any(lesson["number"] == "0001" for lesson in recorded))
        helix = next(item for item in sources["projects"] if item["folder"] == "Helix-Codex")
        self.assertEqual(helix["matrix_id"], "helix-prime")
        self.assertIn("status_file", helix)


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.sources = eng.read_sources(READMES, REMOTE)

    def test_four_tasks_stable_ids(self):
        first = eng.generate_tasks(DAY, self.sources)
        second = eng.generate_tasks(DAY, self.sources)
        self.assertEqual([task["id"] for task in first], [task["id"] for task in second])
        core = [task for task in first if task["kind"] not in {"german", "n8n", "review"}]
        self.assertEqual([task["window"] for task in core], [row[0] for row in eng.WINDOWS])
        self.assertTrue(all(task["minutes"] <= 25 for task in first))
        if not HAS_PROJECTS:
            return
        german = [task for task in first if task["kind"] == "german"]
        self.assertEqual(len(german), 1)
        self.assertTrue(german[0]["links"]["german"])

    def test_check_survives_rebuild(self):
        state = eng.blank_state(DAY)
        task_id = eng.generate_tasks(DAY, self.sources)[0]["id"]
        now = datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc)
        eng.apply_op(state, DAY, self.sources, "check", {"id": task_id}, now)
        view = eng.assemble_day(DAY, self.sources, state, "09:00")
        matched = next(task for task in view["tasks"] if task["id"] == task_id)
        self.assertEqual(matched["status"], "done")

    def test_close_stays_blocked_while_work_is_open(self):
        view = eng.assemble_day(DAY, self.sources, eng.blank_state(DAY), "17:30")
        close = next(task for task in view["tasks"] if task["kind"] == "check")
        self.assertTrue(close["blocked"])
        self.assertNotEqual(view["now_task"], close["id"])

    def test_manual_rejects_long_blocks(self):
        with self.assertRaises(ValueError):
            eng.validate_manual("write the whole architecture", "fajr_dhuhr", 90)
        with self.assertRaises(ValueError):
            eng.validate_manual("ok", "maghrib_isha", 15)

    def test_remove_refuses_generated_task(self):
        state = eng.blank_state(DAY)
        task_id = eng.generate_tasks(DAY, self.sources)[0]["id"]
        now = datetime(2026, 11, 19, 8, 0, tzinfo=eng.CAIRO)
        with self.assertRaises(ValueError):
            eng.apply_op(state, DAY, self.sources, "remove", {"id": task_id}, now)

    def test_round_trip_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-11-19.json"
            state = eng.blank_state(DAY)
            now = datetime(2026, 11, 19, 10, 0, tzinfo=eng.CAIRO)
            eng.apply_op(
                state,
                DAY,
                self.sources,
                "add",
                {"title": "Review one red gate", "window": "asr_maghrib", "minutes": 20},
                now,
            )
            eng.save_state(path, state)
            loaded = eng.load_state(path, DAY)
            self.assertEqual(loaded["manual"][0]["title"], "Review one red gate")
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))
            json.loads(path.read_text(encoding="utf-8"))


class LearningFlowTests(unittest.TestCase):
    def setUp(self):
        self.lessons = eng.read_sources(READMES, REMOTE)["lessons"]

    def test_energy_labels_are_set_and_validated(self):
        sources = eng.read_sources(READMES, REMOTE)
        tasks = eng.generate_tasks(DAY, sources)
        by_kind = {task["kind"]: task for task in tasks}
        self.assertEqual(by_kind["learn"]["energy"], "high")
        if HAS_PROJECTS:
            self.assertEqual(by_kind["german"]["energy"], "low")
        self.assertEqual(by_kind["check"]["energy"], "low")
        clean = eng.validate_manual("A small fix", "fajr_dhuhr", 15, "could", "low")
        self.assertEqual(clean["energy"], "low")
        with self.assertRaises(ValueError):
            eng.validate_manual("A small fix", "fajr_dhuhr", 15, "could", "extreme")

    def test_german_pilot_lessons_are_read(self):
        if not HAS_PROJECTS:
            self.skipTest("project clones not present in this checkout")
        german = eng.read_german(REMOTE)
        self.assertTrue(german["available"])
        self.assertEqual(len(german["lessons"]), 12)
        self.assertTrue(any(item["id"] == "A1-01" for item in german["lessons"]))

    def test_every_domain_has_lessons(self):
        domains = set()
        for lesson in self.lessons:
            self.assertTrue(lesson["domains"], lesson["file"])
            domains.update(lesson["domains"])
        self.assertEqual(
            domains,
            {"Workforce Management", "Governance & Audit", "AI Runtimes", "Tech Stack"},
        )

    def test_lesson_detail_reads_title_and_homework(self):
        detail = eng.lesson_detail(READMES / "lessons", "0018-csat-fcr-sla.html")
        self.assertIn("0018", detail["title"])
        self.assertIn("three headline KPIs", detail["prompt"])

    def test_answer_is_detected_as_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp)
            lesson = next(item for item in self.lessons if item["number"] == "0018")
            now = datetime(2026, 11, 19, 10, 0, tzinfo=eng.CAIRO)
            path = eng.write_answer(records, lesson, "SLA measures access, not quality at all.", now, "SLA measures speed of access, not quality.\nFCR measures resolution without a repeat contact.")
            self.assertTrue(path.is_file())
            self.assertIn("SLA measures access", path.read_text(encoding="utf-8"))
            self.assertIn("0018", path.name)
            recorded = {item.name[:4] for item in records.glob("*.md")}
            self.assertIn("0018", recorded)

    def test_short_answer_rejected(self):
        lesson = self.lessons[0]
        with self.assertRaises(ValueError):
            eng.write_answer(Path("/tmp"), lesson, "too short", datetime.now(eng.CAIRO), "one line\nanother line of memory text here")


class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        self.sources = eng.read_sources(READMES, REMOTE)

    def test_quiz_result_makes_a_lesson_weak(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp)
            now = datetime(2026, 11, 19, 10, 0, tzinfo=eng.CAIRO)
            lesson = self.sources["lessons"][5]
            eng.record_quiz(records, lesson["file"], "q1", False, now)
            quiz = eng.quiz_results(records)
            self.assertEqual(quiz[0]["lesson"], lesson["file"])
            sources = dict(self.sources, quiz=quiz)
            picked = eng.choose_lesson(DAY, sources)
            self.assertEqual(picked["file"], lesson["file"])

    def test_spaced_intervals(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp)
            now = datetime(2026, 11, 19, 10, 0, tzinfo=eng.CAIRO)
            first = eng.grade_term(records, "fail-closed", "again", now)
            self.assertEqual(first["due"], "2026-11-20")
            again = eng.grade_term(records, "fail-closed", "good", now)
            self.assertEqual(again["due"], "2026-11-22")
            later = eng.grade_term(records, "fail-closed", "good", now)
            self.assertEqual(later["due"], "2026-11-26")

    def test_competence_map_has_all_domains(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = eng.competence_map(Path(tmp), self.sources)
            self.assertEqual(len(result["domains"]), 4)
            self.assertEqual(len(result["lessons"]), 24)
            self.assertTrue(result["months"])

    def test_weekly_review_writes_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = eng.build_week_review(
                Path(tmp), DAY, self.sources, "Closed the loop.", "Adaptive lessons"
            )
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn("Weekly review", text)
            self.assertIn("Adaptive lessons", text)


class GapClosureTests(unittest.TestCase):
    def setUp(self):
        self.sources = eng.read_sources(READMES, REMOTE)

    def test_signal_summary_is_honest_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = eng.signal_summary(Path(tmp), dict(self.sources, quiz=[], term_grades={}))
            self.assertEqual(result["level"], "empty")
            self.assertIsNone(result["quiz_accuracy"])

    def test_signal_summary_grows_with_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = datetime(2026, 11, 19, 10, 0, tzinfo=eng.CAIRO)
            attempts = eng.record_quiz(Path(tmp), "0001-fail-closed-gates.html", "q1", True, now)
            result = eng.signal_summary(Path(tmp), dict(self.sources, quiz=attempts))
            self.assertIn(result["level"], {"thin", "growing"})
            self.assertEqual(result["quiz_accuracy"], 1.0)

    def test_export_import_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "from"
            target = Path(tmp) / "to"
            source.mkdir()
            (source / "quiz.json").write_text('{"version":1,"attempts":[]}', encoding="utf-8")
            payload = eng.export_history(source, datetime.now(eng.CAIRO))
            report = eng.validate_import(payload)
            self.assertEqual(report["accepted"], ["quiz.json"])
            written = eng.import_history(target, payload)
            self.assertEqual(written, ["quiz.json"])
            self.assertTrue((target / "quiz.json").is_file())

    def test_import_rejects_unsafe_names(self):
        with self.assertRaises(ValueError):
            eng.validate_import({"version": 1, "kind": "dayos-learning-history", "files": {"../secret": "x"}})

    def test_monthly_rolls_weekly_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "weekly"
            folder.mkdir()
            (folder / "2026-W47.md").write_text(
                "# Weekly review — 2026-W47\nWeek ending 2026-11-19 (Cairo).\n\n"
                "## Recorded this week\n- 0001 Fail-closed gates (2026-11-19)\n\n"
                "## Quiz\n3/5 correct this week.\n\n"
                "## Your note\nok\n\n## Next week's one focus\nAdaptive lessons\n",
                encoding="utf-8",
            )
            result = eng.monthly_reviews(Path(tmp))
            self.assertEqual(result["count"], 1)
            month = result["months"][0]
            self.assertEqual(month["month"], "2026-11")
            self.assertEqual(month["quiz_correct"], 3)
            self.assertEqual(month["focuses"], ["Adaptive lessons"])

    def test_project_task_reflects_the_real_status_file(self):
        """Whatever project the day picks, the task must describe its real files.

        The chosen project changes as the local clones change, so the assertion
        follows the evidence instead of a hard-coded folder: with a status file
        the task quotes it, without one it names the gap and links the note.
        """
        if not HAS_PROJECTS:
            tasks = eng.generate_tasks(DAY, self.sources)
            project = next(task for task in tasks if task["kind"] == "project")
            self.assertIn("No project clones found", project["title"])
            self.assertIn("gap stays visible", project["detail"].lower())
            return
        tasks = eng.generate_tasks(DAY, self.sources)
        project = next(task for task in tasks if task["kind"] == "project")
        self.assertTrue(project["links"]["note"])
        chosen = next(
            item for item in self.sources["projects"]
            if item["folder"] == project["links"]["project"]
        )
        if chosen["status_file"]:
            self.assertIn("status line", project["title"].lower())
            self.assertIn(chosen["status_file"], project["detail"])
        else:
            self.assertIn("no status file", project["title"].lower())
            self.assertIn("gap stays visible", project["detail"])

    def test_project_task_says_gap_when_no_status_file(self):
        """The gap branch is still covered, on a project with no status file."""
        synthetic = dict(self.sources)
        synthetic["projects"] = [
            {
                "folder": "Example-Project",
                "title": "Example Project",
                "blurb": "",
                "status_file": None,
                "status_line": None,
                "matrix_id": None,
                "gap": True,
            }
        ]
        tasks = eng.generate_tasks(DAY, synthetic)
        project = next(task for task in tasks if task["kind"] == "project")
        self.assertIn("no status file", project["title"].lower())
        self.assertTrue(project["links"]["note"])
        self.assertFalse(project["links"].get("matrix_id"))

    def test_note_saves_as_a_daily_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = eng.save_note(Path(tmp), DAY, "Copied the real status line here, no invention.")
            self.assertTrue(path.is_file())
            self.assertIn("Copied the real status line", eng.read_note(Path(tmp), DAY))

    def test_retrieval_requires_two_lines(self):
        self.assertFalse(eng.valid_retrieval("one line only that is quite long indeed"))
        self.assertTrue(eng.valid_retrieval("First remembered line here.\nSecond remembered line here."))


if __name__ == "__main__":
    unittest.main()
