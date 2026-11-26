"""Day engine for Helix-Matrix, the portfolio cockpit.

Reads the project clones and lesson sources, computes Cairo prayer times
offline, and builds a short day of tasks. It does not invent a status the
files do not contain. Missing sources stay missing.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

CAIRO = timezone(timedelta(hours=2))  # Egypt has no daylight saving.
CAIRO_LAT = 30.0444196
CAIRO_LNG = 31.2357116
# Egyptian General Authority of Survey.
FAJR_ANGLE = 19.5
ISHA_ANGLE = 17.5
ASR_FACTOR = 1

WINDOWS = (
    ("fajr_dhuhr", "After Fajr", "fajr", "dhuhr"),
    ("dhuhr_asr", "After Dhuhr", "dhuhr", "asr"),
    ("asr_maghrib", "After Asr", "asr", "maghrib"),
    ("maghrib_isha", "After Maghrib", "maghrib", "isha"),
)
WINDOW_IDS = {row[0] for row in WINDOWS}

MATRIX_IDS = {
    "Helix-Codex": "helix-prime",
    "SigmaHelix-OS": "sigmahelix",
    "live-support-assistant": "live-support",
    "signoff": "signoff",
    "CompliProof": "compliproof",
    "CreateLee": "createlee",
    "Study-Studio": "study-studio",
    "Helix-Education": "helix-ed",
    "L-D-Command-Center": "ld-center",
    "work-samples": "work-samples",
}

STATUS_NAMES = ("SHIPMENT_READINESS.md", "STATUS.md")
README_LIMIT = 4000

# Which portfolio domains each lesson serves. Every domain has lessons, so the
# domain tabs on the matrix page can filter the learning path as well as rows.
LESSON_DOMAINS = {
    "0001": ["Governance & Audit", "AI Runtimes"],
    "0002": ["Governance & Audit"],
    "0003": ["Governance & Audit"],
    "0004": ["Tech Stack", "Governance & Audit"],
    "0005": ["Governance & Audit"],
    "0006": ["Governance & Audit"],
    "0007": ["Tech Stack"],
    "0008": ["Tech Stack"],
    "0009": ["AI Runtimes"],
    "0010": ["Workforce Management"],
    "0011": ["AI Runtimes"],
    "0012": ["Workforce Management"],
    "0013": ["Workforce Management"],
    "0014": ["Workforce Management"],
    "0015": ["Workforce Management"],
    "0016": ["Workforce Management"],
    "0017": ["Workforce Management"],
    "0018": ["Workforce Management"],
    "0019": ["Tech Stack"],
    "0020": ["Tech Stack"],
    "0021": ["Tech Stack"],
    "0022": ["Tech Stack"],
    "0023": ["Tech Stack"],
    "0024": ["AI Runtimes", "Tech Stack"],
}


def _fix(value: float, span: float) -> float:
    value = value % span
    return value + span if value < 0 else value


def _julian(year: int, month: int, day: int) -> float:
    if month <= 2:
        year -= 1
        month += 12
    century = math.floor(year / 100)
    gregorian = 2 - century + math.floor(century / 4)
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + gregorian
        - 1524.5
    )


def _sun_position(jd: float) -> tuple[float, float]:
    days = jd - 2451545.0
    anomaly = _fix(357.529 + 0.98560028 * days, 360)
    mean_long = _fix(280.459 + 0.98564736 * days, 360)
    ecliptic = _fix(
        mean_long
        + 1.915 * math.sin(math.radians(anomaly))
        + 0.020 * math.sin(math.radians(2 * anomaly)),
        360,
    )
    obliquity = 23.439 - 0.00000036 * days
    right_ascension = math.degrees(
        math.atan2(
            math.cos(math.radians(obliquity)) * math.sin(math.radians(ecliptic)),
            math.cos(math.radians(ecliptic)),
        )
    ) / 15
    equation = mean_long / 15 - _fix(right_ascension, 24)
    declination = math.degrees(
        math.asin(math.sin(math.radians(obliquity)) * math.sin(math.radians(ecliptic)))
    )
    return declination, equation


def _hour_angle(latitude: float, declination: float, angle: float) -> float:
    numerator = -math.sin(math.radians(angle)) - math.sin(
        math.radians(latitude)
    ) * math.sin(math.radians(declination))
    denominator = math.cos(math.radians(latitude)) * math.cos(math.radians(declination))
    ratio = numerator / denominator
    if ratio < -1 or ratio > 1:
        raise ValueError(f"sun angle {angle} has no rising time at this latitude")
    return math.degrees(math.acos(ratio)) / 15


def _clock(hours: float) -> str:
    hours = _fix(hours, 24)
    hour = int(hours)
    minute = int(round((hours - hour) * 60))
    if minute == 60:
        hour = (hour + 1) % 24
        minute = 0
    return f"{hour:02d}:{minute:02d}"


def prayer_times(day: date) -> dict[str, str]:
    """Offline Cairo times. Asr uses the standard (Shafi) shadow factor."""
    jd = _julian(day.year, day.month, day.day) - CAIRO_LNG / 360.0
    declination, equation = _sun_position(jd)
    midday = _fix(12 - equation, 24)
    asr_angle = -math.degrees(
        math.atan2(
            1,
            ASR_FACTOR + math.tan(math.radians(abs(CAIRO_LAT - declination))),
        )
    )
    shift = 2 - CAIRO_LNG / 15.0

    def local(hours: float) -> str:
        return _clock(hours + shift)

    return {
        "fajr": local(midday - _hour_angle(CAIRO_LAT, declination, FAJR_ANGLE)),
        "sunrise": local(midday - _hour_angle(CAIRO_LAT, declination, 0.833)),
        "dhuhr": local(midday),
        "asr": local(midday + _hour_angle(CAIRO_LAT, declination, asr_angle)),
        "maghrib": local(midday + _hour_angle(CAIRO_LAT, declination, 0.833)),
        "isha": local(midday + _hour_angle(CAIRO_LAT, declination, ISHA_ANGLE)),
    }


def _minutes(clock: str) -> int:
    hour, minute = clock.split(":")
    return int(hour) * 60 + int(minute)


def windows_for(prayers: dict[str, str]) -> list[dict]:
    rows = []
    for window_id, label, start_key, end_key in WINDOWS:
        rows.append(
            {
                "id": window_id,
                "label": label,
                "start": prayers[start_key],
                "end": prayers[end_key],
                "start_min": _minutes(prayers[start_key]),
                "end_min": _minutes(prayers[end_key]),
            }
        )
    return rows


def current_window(prayers: dict[str, str], now_clock: str) -> str | None:
    now = _minutes(now_clock)
    for row in windows_for(prayers):
        if row["start_min"] <= now < row["end_min"]:
            return row["id"]
    return None


class _GlossaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_dt = False
        self._in_b = False
        self._in_dd = False
        self._buf: list[str] = []
        self._term: str | None = None
        self.terms: list[dict] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "dt":
            self._in_dt = True
        elif tag == "b" and self._in_dt:
            self._in_b = True
            self._buf = []
        elif tag == "dd":
            self._in_dd = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "b" and self._in_b:
            self._term = "".join(self._buf).strip()
            self._in_b = False
        elif tag == "dt":
            self._in_dt = False
        elif tag == "dd" and self._in_dd:
            definition = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if self._term and definition:
                self.terms.append({"term": self._term, "definition": definition})
            self._term = None
            self._in_dd = False

    def handle_data(self, data: str) -> None:
        if self._in_b or self._in_dd:
            self._buf.append(data)


def parse_glossary(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    parser = _GlossaryParser()
    parser.feed(path.read_text(encoding="utf-8"))
    if not parser.terms:
        raise ValueError(f"no glossary terms in {path}")
    return parser.terms


_LESSON_LINE = re.compile(r"^\d+\.\s+(\S+\.html)\s+[—-]\s+(.+)$")


def parse_lessons(index_path: Path, records_dir: Path) -> list[dict]:
    if not index_path.is_file():
        raise FileNotFoundError(index_path)
    recorded = set()
    if records_dir.is_dir():
        for record in records_dir.glob("*.md"):
            recorded.add(record.name[:4])
    lessons = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = _LESSON_LINE.match(line.strip())
        if not match:
            continue
        filename, title = match.group(1), match.group(2).strip()
        number = filename[:4]
        lessons.append(
            {
                "file": filename,
                "title": title,
                "number": number,
                "recorded": number in recorded,
                "domains": LESSON_DOMAINS.get(number, []),
            }
        )
    if not lessons:
        raise ValueError(f"no lessons in {index_path}")
    return lessons


def _first_status_line(path: Path) -> str | None:
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip().lstrip("#").strip()
        if text and not text.startswith("```"):
            return text[:240]
    return None


def resolve_projects(app_root: Path) -> Path:
    """Find the folder that holds the project clones.

    Precedence: ``HELIX_MATRIX_PROJECTS``, then ``../remotely-active``, then
    ``../../remotely-active`` (the layout used when the app lives inside the
    owner's workspace), then the first candidate even if it does not exist yet
    so the caller can report a real path instead of a guess.
    """
    override = os.environ.get("HELIX_MATRIX_PROJECTS")
    if override:
        return Path(override).expanduser()
    candidates = (
        app_root.parent / "remotely-active",
        app_root.parent.parent / "remotely-active",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def scan_projects(root: Path) -> list[dict]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    projects = []
    for child in sorted(path for path in root.iterdir() if path.is_dir()):
        if child.name.startswith("."):
            continue
        readme = child / "README.md"
        title = child.name
        blurb = ""
        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="replace")[:README_LIMIT]
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if lines and lines[0].startswith("#"):
                title = lines[0].lstrip("#").strip() or child.name
            paragraphs = [line for line in lines if not line.startswith("#")]
            blurb = " ".join(paragraphs[:3])[:360]
        status_name = next((name for name in STATUS_NAMES if (child / name).is_file()), None)
        status_line = _first_status_line(child / status_name) if status_name else None
        projects.append(
            {
                "folder": child.name,
                "title": title,
                "blurb": blurb,
                "status_file": status_name,
                "status_line": status_line,
                "matrix_id": MATRIX_IDS.get(child.name),
                "gap": status_name is None,
            }
        )
    if not projects:
        raise ValueError(f"no projects in {root}")
    return projects


def _task(
    day: date,
    *,
    kind: str,
    window: str,
    minutes: int,
    title: str,
    source: str,
    detail: str,
    links: dict,
    priority: str = "should",
    energy: str = "medium",
) -> dict:
    key = f"{day.isoformat()}|{kind}|{source}|{window}"
    return {
        "id": hashlib.sha256(key.encode()).hexdigest()[:16],
        "kind": kind,
        "window": window,
        "minutes": minutes,
        "title": title,
        "source": source,
        "detail": detail,
        "links": links,
        "priority": priority,
        "energy": energy,
        "manual": False,
    }


QUIZ_FILE = "quiz.json"
TERMS_FILE = "terms.json"
INTERVALS = (1, 3, 7, 14, 30)
_RECORDED_LINE = re.compile(r"Recorded:\s*(\d{4}-\d{2}-\d{2})")


def _load_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return json.loads(json.dumps(default))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(default))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def quiz_results(records_dir: Path) -> list[dict]:
    return _load_json(records_dir / QUIZ_FILE, {"version": 1, "attempts": []}).get("attempts", [])


def record_quiz(records_dir: Path, lesson_file: str, question: str, correct: bool, now: datetime) -> list[dict]:
    if not lesson_file.endswith(".html") or "/" in lesson_file or "\\" in lesson_file:
        raise ValueError("bad lesson name")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,20}", question):
        raise ValueError("bad question id")
    data = _load_json(records_dir / QUIZ_FILE, {"version": 1, "attempts": []})
    data.setdefault("attempts", []).append(
        {
            "lesson": lesson_file,
            "question": question,
            "correct": bool(correct),
            "at": now.astimezone(CAIRO).isoformat(timespec="minutes"),
        }
    )
    _write_json(records_dir / QUIZ_FILE, data)
    return data["attempts"]


def lesson_scores(attempts: list[dict]) -> dict[str, dict]:
    scores: dict[str, dict] = {}
    for attempt in attempts:
        number = str(attempt.get("lesson", ""))[:4]
        if not number.isdigit():
            continue
        row = scores.setdefault(number, {"correct": 0, "wrong": 0})
        row["correct" if attempt.get("correct") else "wrong"] += 1
    return scores


def choose_lesson(day: date, sources: dict) -> dict:
    """Weakest unrecorded lesson first; recorded-but-weak ones become a review task."""
    lessons = sources["lessons"]
    scores = lesson_scores(sources.get("quiz", []))
    unfinished = [lesson for lesson in lessons if not lesson["recorded"]] or lessons
    weak = []
    for lesson in unfinished:
        row = scores.get(lesson["number"], {"correct": 0, "wrong": 0})
        if row["wrong"]:
            ratio = row["wrong"] / (row["wrong"] + row["correct"])
            weak.append((ratio, row["wrong"], lesson))
    if weak:
        weak.sort(key=lambda item: (-item[0], -item[1], item[2]["number"]))
        return weak[0][2]
    return unfinished[day.toordinal() % len(unfinished)]


def review_lessons(sources: dict) -> list[dict]:
    scores = lesson_scores(sources.get("quiz", []))
    rows = []
    for lesson in sources["lessons"]:
        row = scores.get(lesson["number"], {"correct": 0, "wrong": 0})
        if lesson["recorded"] and row["wrong"]:
            rows.append((row["wrong"], lesson))
    rows.sort(key=lambda item: (-item[0], item[1]["number"]))
    return [lesson for _, lesson in rows]


def term_grades(records_dir: Path) -> dict:
    return _load_json(records_dir / TERMS_FILE, {"version": 1, "grades": {}}).get("grades", {})


def grade_term(records_dir: Path, term: str, grade: str, now: datetime) -> dict:
    if grade not in {"again", "good", "easy"}:
        raise ValueError("grade must be again, good or easy")
    term = " ".join(str(term).split())[:120]
    if not term:
        raise ValueError("term is required")
    data = _load_json(records_dir / TERMS_FILE, {"version": 1, "grades": {}})
    grades = data.setdefault("grades", {})
    row = grades.get(term, {"level": 0, "seen": 0, "missed": 0})
    today = now.astimezone(CAIRO).date()
    if grade == "again":
        level, missed = 0, row.get("missed", 0) + 1
    elif grade == "good":
        level, missed = min(row.get("level", 0) + 1, len(INTERVALS) - 1), row.get("missed", 0)
    else:
        level, missed = min(row.get("level", 0) + 2, len(INTERVALS) - 1), row.get("missed", 0)
    grades[term] = {
        "level": level,
        "seen": row.get("seen", 0) + 1,
        "missed": missed,
        "due": (today + timedelta(days=INTERVALS[level])).isoformat(),
        "last": today.isoformat(),
    }
    _write_json(records_dir / TERMS_FILE, data)
    return grades[term]


def due_terms(day: date, sources: dict) -> list[dict]:
    grades = sources.get("term_grades", {})
    rows = []
    for term in sources["terms"]:
        row = grades.get(term["term"]) or {}
        due = row.get("due", "0000")
        if due <= day.isoformat():
            rows.append((due, term["term"], term))
    rows.sort()
    return [item[2] for item in rows]


def choose_term(day: date, sources: dict) -> dict:
    due = due_terms(day, sources)
    if due:
        return due[0]
    terms = sources["terms"]
    return terms[day.toordinal() % len(terms)]


def _answer_dates(records_dir: Path) -> dict[str, str]:
    dates = {}
    if not records_dir.is_dir():
        return dates
    for path in records_dir.glob("[0-9][0-9][0-9][0-9]-*.md"):
        found = _RECORDED_LINE.search(path.read_text(encoding="utf-8", errors="replace"))
        if found:
            dates[path.name[:4]] = found.group(1)
    return dates


def competence_map(records_dir: Path, sources: dict) -> dict:
    """Lessons recorded per domain per month — growth you can actually see."""
    dates = _answer_dates(records_dir)
    scores = lesson_scores(sources.get("quiz", []))
    months = sorted({value[:7] for value in dates.values()})
    if not months:
        months = [datetime.now(CAIRO).strftime("%Y-%m")]
    domains = sorted({d for lesson in sources["lessons"] for d in lesson["domains"]})
    rows = []
    for domain in domains:
        cells = []
        for month in months:
            count = 0
            for lesson in sources["lessons"]:
                if domain in lesson["domains"] and dates.get(lesson["number"], "")[:7] == month:
                    count += 1
            cells.append(count)
        rows.append({"domain": domain, "months": cells, "total": sum(cells)})
    lessons = []
    for lesson in sources["lessons"]:
        row = scores.get(lesson["number"], {"correct": 0, "wrong": 0})
        total = row["correct"] + row["wrong"]
        lessons.append(
            {
                "number": lesson["number"],
                "title": lesson["title"],
                "domains": lesson["domains"],
                "recorded": bool(dates.get(lesson["number"])),
                "recorded_on": dates.get(lesson["number"]),
                "accuracy": round(row["correct"] / total, 2) if total else None,
            }
        )
    return {"months": months, "domains": rows, "lessons": lessons}


def lesson_pick_reason(sources: dict) -> str:
    scores = lesson_scores(sources.get("quiz", []))
    weak = [item for item in scores.values() if item.get("wrong", 0)]
    if weak:
        return "Chosen because you missed a quiz question — the map has real signal."
    return "Chosen by the day's order. Answer quizzes to give the map real signal."


def signal_summary(records_dir: Path, sources: dict) -> dict:
    """How much real evidence exists — never invented to look healthy."""
    quiz = sources.get("quiz", [])
    answers = list(records_dir.glob("[0-9][0-9][0-9][0-9]-*.md")) if records_dir.is_dir() else []
    grades = sources.get("term_grades", {})
    weekly = list((records_dir / "weekly").glob("*.md")) if (records_dir / "weekly").is_dir() else []
    decisions = []
    decision_file = records_dir / "metacognition" / "decisions.json"
    if decision_file.is_file():
        try:
            decisions = json.loads(decision_file.read_text(encoding="utf-8")).get("decisions", [])
        except (ValueError, OSError):
            decisions = []
    correct = sum(1 for item in quiz if item.get("correct"))
    total = len(quiz)
    points = total + len(answers) + len(grades) + len(decisions)
    level = "empty" if points == 0 else "thin" if points < 5 else "growing" if points < 20 else "solid"
    return {
        "level": level,
        "quiz_attempts": total,
        "quiz_accuracy": round(correct / total, 2) if total else None,
        "written_answers": len(answers),
        "graded_terms": len(grades),
        "weekly_reviews": len(weekly),
        "approved_decisions": len(decisions),
        "note": (
            "No real effort recorded yet. The adaptive picks fall back to the day's order."
            if level == "empty" else
            "Signal is building. Quiz misses now change which lesson comes next."
        ),
    }


_WEEK_END = re.compile(r"Week ending (\d{4}-\d{2}-\d{2})")
_QUIZ_LINE = re.compile(r"(\d+)/(\d+) correct this week")


def monthly_reviews(records_dir: Path) -> dict:
    """Roll weekly reviews into a month-by-month trend line."""
    folder = records_dir / "weekly"
    months: dict[str, dict] = {}
    if folder.is_dir():
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            found = _WEEK_END.search(text)
            month = found.group(1)[:7] if found else path.name[:4] + "-01"
            row = months.setdefault(
                month,
                {"month": month, "reviews": 0, "recorded": 0, "quiz_correct": 0, "quiz_total": 0, "focuses": []},
            )
            row["reviews"] += 1
            quiz = _QUIZ_LINE.search(text)
            if quiz:
                row["quiz_correct"] += int(quiz.group(1))
                row["quiz_total"] += int(quiz.group(2))
            section = re.search(r"## Recorded this week\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
            if section:
                row["recorded"] += len(re.findall(r"^- \d{4}", section.group(1), re.MULTILINE))
            focus = re.search(r"## Next week's one focus\n(.+?)(?:\n|$)", text)
            if focus and focus.group(1).strip() and not focus.group(1).strip().startswith("- ("):
                row["focuses"].append(focus.group(1).strip())
    rows = sorted(months.values(), key=lambda item: item["month"])
    return {"months": rows, "count": len(rows)}


def _safe_record_name(name: str) -> bool:
    if not name or name.startswith(".") or ".." in name or name.startswith("/"):
        return False
    parts = name.split("/")
    return all(part and not part.startswith(".") and "\\" not in part for part in parts)


def export_history(records_dir: Path, now: datetime) -> dict:
    """A portable, plain-text copy of the learning history — no secrets."""
    files: dict[str, str] = {}
    if records_dir.is_dir():
        for path in sorted(records_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".json", ".md"}:
                continue
            relative = path.relative_to(records_dir).as_posix()
            if _safe_record_name(relative):
                files[relative] = path.read_text(encoding="utf-8", errors="replace")
    return {
        "version": 1,
        "kind": "dayos-learning-history",
        "exported_at": now.astimezone(CAIRO).isoformat(timespec="minutes"),
        "files": files,
    }


def validate_import(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("kind") != "dayos-learning-history":
        raise ValueError("not a Day OS learning-history file")
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("no records in this file")
    accepted, rejected = [], []
    for name, body in files.items():
        if _safe_record_name(name) and isinstance(body, str) and len(body) <= 200_000:
            accepted.append(name)
        else:
            rejected.append(str(name))
    if not accepted:
        raise ValueError("no safe records in this file")
    return {"accepted": accepted, "rejected": rejected, "bytes": sum(len(files[n]) for n in accepted)}


def import_history(records_dir: Path, data: dict) -> list[str]:
    """Merge a validated history in. Existing files are replaced, never deleted."""
    report = validate_import(data)
    written = []
    for name in report["accepted"]:
        target = records_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(data["files"][name], encoding="utf-8")
        temporary.replace(target)
        written.append(name)
    return written


def iso_week(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def review_path(records_dir: Path, day: date) -> Path:
    return records_dir / "weekly" / f"{iso_week(day)}.md"


def build_week_review(records_dir: Path, day: date, sources: dict, note: str = "", focus: str = "") -> Path:
    """Close the week: record what was learned, what slipped and one next focus."""
    dates = _answer_dates(records_dir)
    attempts = [
        item for item in sources.get("quiz", [])
        if str(item.get("at", ""))[:10] >= (day - timedelta(days=6)).isoformat()
    ]
    correct = sum(1 for item in attempts if item.get("correct"))
    recorded = []
    for lesson in sources["lessons"]:
        stamp = dates.get(lesson["number"], "")
        if stamp and (day - timedelta(days=6)).isoformat() <= stamp <= day.isoformat():
            recorded.append(f"- {lesson['number']} {lesson['title']} ({stamp})")
    grades = sources.get("term_grades", {})
    missed_terms = [term for term, row in grades.items() if row.get("missed", 0) and row.get("last", "")[:10] >= (day - timedelta(days=6)).isoformat()]
    body = (
        f"# Weekly review — {iso_week(day)}\n\n"
        f"Week ending {day.isoformat()} (Cairo).\n\n"
        f"## Recorded this week\n" + ("\n".join(recorded) if recorded else "- Nothing recorded. Gap left open.\n") + "\n\n"
        f"## Quiz\n{correct}/{len(attempts)} correct this week.\n\n"
        f"## Terms that needed another look\n" + ("\n".join(f"- {term}" for term in missed_terms) if missed_terms else "- None flagged.\n") + "\n\n"
        f"## Your note\n{note or '- (no note)'}\n\n"
        f"## Next week's one focus\n{focus or '- (not set)'}\n"
    )
    path = review_path(records_dir, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".md.tmp")
    temporary.write_text(body, encoding="utf-8")
    temporary.replace(path)
    return path


def read_german(projects: Path) -> dict:
    """Read the pilot lessons of the separate Mannschaft app, read-only."""
    root = projects / "Mannschaft"
    lessons_dir = root / "content" / "lessons"
    lessons = []
    if lessons_dir.is_dir():
        for path in sorted(lessons_dir.glob("*.lesson.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                title = data.get("title", {}) or {}
                lessons.append(
                    {
                        "id": data.get("id", path.name[:5]),
                        "title": title.get("en") or title.get("de") or path.name,
                        "minutes": data.get("minutes", 0),
                    }
                )
            except (ValueError, OSError):
                continue
    return {"root": str(root), "lessons": lessons, "available": root.is_dir()}


def generate_tasks(day: date, sources: dict) -> list[dict]:
    """Adaptive day: lesson, German, glossary, project and day check."""
    lessons = sources["lessons"]
    lesson = choose_lesson(day, sources)
    german = sources.get("german", {})
    german_lesson = german.get("lessons", [])
    term = choose_term(day, sources)
    projects = sources["projects"]
    if projects:
        project = projects[day.toordinal() % len(projects)]
        status_bit = (
            project["status_line"]
            if project["status_line"]
            else "No SHIPMENT_READINESS.md or STATUS.md. The gap stays visible."
        )
        project_task = _task(
            day,
            kind="project",
                energy="medium",
            window="asr_maghrib",
            minutes=20,
            title=(
                f"{project['folder']}: copy the status line into today's note."
                if project["status_file"]
                else f"{project['folder']}: no status file exists — record the gap in today's note, do not invent a status."
            ),
            source=f"remotely-active/{project['folder']}",
            detail=(
                f"{project['status_file']}: {status_bit}"
                if project["status_file"]
                else f"No {STATUS_NAMES[0]} or {STATUS_NAMES[1]} in remotely-active/{project['folder']}. The gap stays visible."
            ),
            links={
                "lesson": None,
                "project": project["folder"],
                "matrix_id": project["matrix_id"],
                "term": term["term"],
                "note": day.isoformat(),
            },
        )
    else:
        project_task = _task(
            day,
            kind="project",
                energy="medium",
            window="asr_maghrib",
            minutes=20,
            title="No project clones found — point HELIX_MATRIX_PROJECTS at your remotely-active folder, then record the gap in today's note.",
            source="remotely-active (not found)",
            detail="The day OS reads live status files from the project clones; with none present, the gap stays visible instead of inventing a status.",
            links={
                "lesson": None,
                "project": None,
                "matrix_id": None,
                "term": term["term"],
                "note": day.isoformat(),
            },
        )
    return [
        _task(
            day,
            kind="learn",
                energy="high",
            window="fajr_dhuhr",
            minutes=20,
            title=f"Lesson {lesson['number']}: do the quiz, then write one sentence in your own words.",
            source=f"lessons/{lesson['file']}",
            detail=lesson["title"],
            links={"lesson": lesson["file"], "project": None, "matrix_id": None},
        ),
        *(
            [
                _task(
                    day,
                    kind="german",
                energy="low",
                    window="fajr_dhuhr",
                    minutes=10,
                    title=(
                        "German v5: listen to one pilot lesson — " +
                        german_lesson[day.toordinal() % len(german_lesson)]["title"]
                    ),
                    source="Mannschaft",
                    detail="12 hand-authored lessons, A1 to C2. Start the app on port 8766 if it is not live.",
                    links={"lesson": None, "project": None, "matrix_id": None, "german": True},
                    priority="could",
                )
            ] if german_lesson else []
        ),
        _task(
            day,
            kind="n8n",
            window="asr_maghrib",
            minutes=10,
            title="n8n: check the live service and name one open blocker.",
            source="n8n-production",
            detail="88% deployed on the real host; Cloudflare Access, Trivy and host reinstall still open.",
            links={"lesson": None, "project": None, "matrix_id": None, "n8n": True},
            priority="could",
            energy="low",
        ),
        _task(
            day,
            kind="glossary",
                energy="medium",
            window="dhuhr_asr",
            minutes=15,
            title=f"Cover the definition of “{term['term']}” and write it back in one line.",
            source="reference/glossary.html",
            detail=term["definition"],
            links={"lesson": None, "project": None, "matrix_id": None, "term": term["term"], "glossary": True},
        ),
        *[
            _task(
                day,
                kind="review",
                energy="medium",
                window="dhuhr_asr",
                minutes=10,
                title=f"Review {item['number']}: you got a quiz question wrong after recording it.",
                source=f"review/{item['number']}",
                detail=item["title"],
                links={"lesson": item["file"], "project": None, "matrix_id": None},
                priority="must",
            )
            for item in review_lessons(sources)[:1]
        ],
        project_task,
        _task(
            day,
            kind="check",
                energy="low",
            window="maghrib_isha",
            minutes=10,
            title="Before Isha: every task above is done or skipped. An open task is not finished.",
            source="learning-records/day-os",
            detail="Day check. This is the only task in the Maghrib window.",
            links={"lesson": None, "project": None, "matrix_id": None},
        ),
    ]


def blank_state(day: date) -> dict:
    return {"version": 1, "date": day.isoformat(), "statuses": {}, "manual": []}


def load_state(path: Path, day: date) -> dict:
    if not path.is_file():
        return blank_state(day)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("date") != day.isoformat() or data.get("version") != 1:
        raise ValueError(f"state file {path} is not version 1 for {day.isoformat()}")
    data.setdefault("statuses", {})
    data.setdefault("manual", [])
    return data


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


_HOMEWORK = re.compile(
    r"Homework[^<]*</h2>\s*<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL
)
_TAG = re.compile(r"<[^>]+>")


def lesson_detail(lessons_dir: Path, filename: str) -> dict:
    """Title and homework prompt for one lesson, read from the lesson file."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("bad lesson name")
    if not filename.endswith(".html"):
        raise ValueError("lesson must be an html file")
    path = lessons_dir / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    html = path.read_text(encoding="utf-8", errors="replace")
    heading = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    title = _TAG.sub("", heading.group(1)).strip() if heading else filename
    prompt = ""
    found = _HOMEWORK.search(html)
    if found:
        prompt = re.sub(r"\s+", " ", _TAG.sub("", found.group(1))).strip()
    return {"file": filename, "title": title, "prompt": prompt}


def answer_path(records_dir: Path, lesson_number: str) -> Path:
    """One learning record per lesson number: the engine counts it as done."""
    if not re.fullmatch(r"\d{4}", lesson_number):
        raise ValueError("bad lesson number")
    return records_dir / f"{lesson_number}-my-answer.md"


def note_path(records_dir: Path, day: date) -> Path:
    return records_dir / "day-notes" / f"{day.isoformat()}.md"


def read_note(records_dir: Path, day: date) -> str:
    path = note_path(records_dir, day)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def save_note(records_dir: Path, day: date, text: str) -> Path:
    text = text.strip()
    if len(text) < 10:
        raise ValueError("write at least a sentence (10 characters)")
    if len(text) > 8000:
        raise ValueError("note is too long (8000 characters max)")
    path = note_path(records_dir, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".md.tmp")
    temporary.write_text(
        f"# Note — {day.isoformat()}\n\n{text}\n", encoding="utf-8"
    )
    temporary.replace(path)
    return path


def valid_retrieval(text: str) -> bool:
    """Two lines written from memory before the lesson prompt is revealed."""
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return len(lines) >= 2 and sum(len(line) for line in lines) >= 40


def write_answer(records_dir: Path, lesson: dict, answer: str, now: datetime, retrieval: str = "") -> Path:
    """Save the final answer as a learning record. Idempotent per lesson."""
    if not valid_retrieval(retrieval):
        raise ValueError("write two lines from memory before the answer")
    answer = " ".join(answer.split())
    if len(answer) < 20:
        raise ValueError("write at least one full sentence (20 characters)")
    if len(answer) > 8000:
        raise ValueError("answer is too long (8000 characters max)")
    retrieval_lines = [line.strip() for line in retrieval.splitlines() if line.strip()]
    path = answer_path(records_dir, lesson["number"])
    stamp = now.astimezone(CAIRO).strftime("%Y-%m-%d %H:%M %Z")
    body = (
        f"# Learning record — {lesson['number']} {lesson['title']}\n\n"
        f"{answer}\n\n"
        f"## Retrieval before looking\n" +
        "\n".join(f"- {line}" for line in retrieval_lines) + "\n\n"
        f"- **Lesson:** lessons/{lesson['file']}\n"
        f"- **Recorded:** {stamp}\n"
        f"- **Status:** done — written in my own words, not copied.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".md.tmp")
    temporary.write_text(body, encoding="utf-8")
    temporary.replace(path)
    return path


def _apply_status(task: dict, statuses: dict) -> dict:
    saved = statuses.get(task["id"], {})
    status = saved.get("status", "open")
    if status not in {"open", "done", "skipped"}:
        status = "open"
    task = dict(task)
    task["status"] = status
    task["checked_at"] = saved.get("checked_at")
    return task


def assemble_day(
    day: date,
    sources: dict,
    state: dict,
    now_clock: str,
    *,
    day_os_dir: Path | None = None,
) -> dict:
    prayers = prayer_times(day)
    generated = [_apply_status(task, state["statuses"]) for task in generate_tasks(day, sources)]
    manual = []
    for item in state["manual"]:
        manual.append(_apply_status(item, state["statuses"]))
    tasks = generated + manual
    open_other = [task for task in tasks if task["kind"] != "check" and task["status"] == "open"]
    for task in tasks:
        if task["kind"] == "check":
            task["blocked"] = bool(open_other)
    window = current_window(prayers, now_clock)
    now_task = None
    ordered = [row[0] for row in WINDOWS]
    search_from = ordered.index(window) if window in ordered else 0
    for window_id in ordered[search_from:] + ordered[:search_from]:
        for task in tasks:
            if task["window"] == window_id and task["status"] == "open" and not task.get("blocked"):
                now_task = task["id"]
                break
        if now_task:
            break
    streak = (
        compute_streak(day_os_dir, day, sources)
        if day_os_dir is not None
        else {"count": 0, "last_complete": None, "today_complete": False}
    )
    by_matrix: dict[str, list[str]] = {}
    for project in sources["projects"]:
        matrix_id = project.get("matrix_id")
        if matrix_id:
            by_matrix[matrix_id] = tasks_for_matrix(matrix_id, tasks)
    return {
        "date": day.isoformat(),
        "timezone": "Africa/Cairo",
        "now": now_clock,
        "prayers": prayers,
        "windows": windows_for(prayers),
        "current_window": window,
        "now_task": now_task,
        "tasks": tasks,
        "streak": streak,
        "matrix_tasks": by_matrix,
        "counts": {
            "lessons": len(sources["lessons"]),
            "unrecorded_lessons": sum(1 for lesson in sources["lessons"] if not lesson["recorded"]),
            "terms": len(sources["terms"]),
            "projects": len(sources["projects"]),
            "open": sum(1 for task in tasks if task["status"] == "open"),
            "done": sum(1 for task in tasks if task["status"] == "done"),
            "skipped": sum(1 for task in tasks if task["status"] == "skipped"),
            "quiz_attempts": len(sources.get("quiz", [])),
            "due_terms": len(due_terms(day, sources)),
        },
        "projects": sources["projects"],
        "lessons": sources["lessons"],
        "due_term_list": [item["term"] for item in due_terms(day, sources)][:8],
        "review_lessons": [item["file"] for item in review_lessons(sources)[:3]],
        "german": sources.get("german", {}),
        "live": True,
    }


def validate_manual(title: str, window: str, minutes: int, priority: str = "should", energy: str = "medium") -> dict:
    title = " ".join(title.split())
    if not 3 <= len(title) <= 140:
        raise ValueError("title must be 3 to 140 characters")
    if window not in WINDOW_IDS or window == "maghrib_isha":
        raise ValueError("window must be a work window before Maghrib")
    if minutes not in {10, 15, 20, 25}:
        raise ValueError("minutes must be 10, 15, 20 or 25")
    if priority not in {"must", "should", "could"}:
        raise ValueError("priority must be must, should or could")
    if energy not in {"low", "medium", "high"}:
        raise ValueError("energy must be low, medium or high")
    return {"title": title, "window": window, "minutes": minutes, "priority": priority, "energy": energy}


def apply_op(state: dict, day: date, sources: dict, op: str, payload: dict, now: datetime) -> dict:
    known = {task["id"]: task for task in generate_tasks(day, sources)}
    for item in state["manual"]:
        known[item["id"]] = item
    stamp = now.astimezone(CAIRO).isoformat(timespec="minutes")

    if op in {"check", "uncheck", "skip"}:
        task_id = str(payload.get("id", ""))
        if task_id not in known:
            raise ValueError("unknown task")
        if op == "uncheck":
            state["statuses"].pop(task_id, None)
        else:
            state["statuses"][task_id] = {
                "status": "done" if op == "check" else "skipped",
                "checked_at": stamp,
            }
        return state

    if op == "add":
        clean = validate_manual(
            str(payload.get("title", "")),
            str(payload.get("window", "")),
            int(payload.get("minutes", 0)),
            str(payload.get("priority", "should")),
            str(payload.get("energy", "medium")),
        )
        digest = hashlib.sha256(f"{stamp}|{clean['title']}".encode()).hexdigest()[:16]
        state["manual"].append(
            {
                "id": f"manual-{digest}",
                "kind": "manual",
                "window": clean["window"],
                "minutes": clean["minutes"],
                "title": clean["title"],
                "source": "added by you",
                "detail": "Manual task. It stays on this day only.",
                "priority": clean["priority"],
                "energy": clean["energy"],
                "links": {"lesson": None, "project": None, "matrix_id": None},
                "manual": True,
            }
        )
        return state

    if op == "remove":
        task_id = str(payload.get("id", ""))
        before = len(state["manual"])
        state["manual"] = [item for item in state["manual"] if item["id"] != task_id]
        if len(state["manual"]) == before:
            raise ValueError("only a task you added can be removed")
        state["statuses"].pop(task_id, None)
        return state

    raise ValueError("op must be check, uncheck, skip, add or remove")


def clock_in(moment: datetime) -> str:
    local = moment.astimezone(CAIRO)
    return f"{local.hour:02d}:{local.minute:02d}"


def read_sources(readmes: Path, remote: Path) -> dict:
    records = readmes / "learning-records"
    projects = scan_projects(remote) if remote.is_dir() else []
    return {
        "terms": parse_glossary(readmes / "reference" / "glossary.html"),
        "lessons": parse_lessons(readmes / "lessons" / "INDEX.md", records),
        "projects": projects,
        "quiz": quiz_results(records),
        "term_grades": term_grades(records),
        "german": read_german(remote),
    }


def day_complete(state: dict, day: date, sources: dict) -> bool:
    """A day counts only when the Maghrib check is marked done."""
    view = assemble_day(day, sources, state, "23:59")
    check = next((task for task in view["tasks"] if task["kind"] == "check"), None)
    return bool(check and check["status"] == "done")


def compute_streak(day_os_dir: Path, day: date, sources: dict) -> dict:
    """Count consecutive completed days ending on today or yesterday.

    Incomplete today does not break yesterday's streak. Missing files are gaps.
    """
    if not day_os_dir.is_dir():
        return {"count": 0, "last_complete": None, "today_complete": False}

    cursor = day
    today_state_path = day_os_dir / f"{day.isoformat()}.json"
    today_complete = False
    if today_state_path.is_file():
        try:
            today_complete = day_complete(load_state(today_state_path, day), day, sources)
        except (ValueError, json.JSONDecodeError, OSError):
            today_complete = False
    if not today_complete:
        cursor = day - timedelta(days=1)

    count = 0
    last_complete = None
    while True:
        path = day_os_dir / f"{cursor.isoformat()}.json"
        if not path.is_file():
            break
        try:
            state = load_state(path, cursor)
            if not day_complete(state, cursor, sources):
                break
        except (ValueError, json.JSONDecodeError, OSError):
            break
        count += 1
        last_complete = cursor.isoformat()
        cursor = cursor - timedelta(days=1)

    return {
        "count": count,
        "last_complete": last_complete,
        "today_complete": today_complete,
    }


def tasks_for_matrix(matrix_id: str | None, tasks: list[dict]) -> list[str]:
    if not matrix_id:
        return []
    return [
        task["id"]
        for task in tasks
        if (task.get("links") or {}).get("matrix_id") == matrix_id
    ]


