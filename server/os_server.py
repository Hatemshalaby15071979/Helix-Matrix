"""Helix-Matrix local server. Binds to 127.0.0.1 only.

Serves the Helix-Matrix page and reads two places:

  this repository  (lessons, glossary, learning records, metacognition memory)
  the project folder (default ../remotely-active — one clone per GitHub repo)

Run from anywhere:

  python3 server/os_server.py

Environment:

  HELIX_MATRIX_PROJECTS  folder holding the project clones (default ../remotely-active)
  HELIX_MATRIX_HOST      bind address (default 127.0.0.1 — loopback only)
  HELIX_MATRIX_PORT      port (default 8765)
"""

from __future__ import annotations

import html
import json
import os
import sys
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen

from os_engine import (
    CAIRO,
    apply_op,
    assemble_day,
    build_week_review,
    clock_in,
    competence_map,
    due_terms,
    generate_tasks,
    grade_term,
    export_history,
    import_history,
    iso_week,
    lesson_detail,
    lesson_pick_reason,
    load_state,
    monthly_reviews,
    prayer_times,
    read_note,
    read_sources,
    resolve_projects,
    record_quiz,
    review_path,
    save_note,
    save_state,
    signal_summary,
    validate_import,
    valid_retrieval,
    write_answer,
)

APP = Path(__file__).resolve().parent.parent
READMES = APP
REMOTE = resolve_projects(APP)
HOST = os.environ.get("HELIX_MATRIX_HOST", "127.0.0.1")
PORT = int(os.environ.get("HELIX_MATRIX_PORT", "8765"))
MAX_BODY = 16_384

STATIC_ROOTS = {
    "": APP / "app",
    "assets": APP / "assets",
    "lessons": APP / "lessons",
    "reference": APP / "reference",
}
ALLOWED_SUFFIXES = {".html", ".css", ".js", ".md", ".svg"}
INDEX_PAGE = APP / "app" / "index.html"


def day_os_dir() -> Path:
    return READMES / "learning-records" / "day-os"


def records_dir() -> Path:
    return READMES / "learning-records"


def excerpts_path() -> Path:
    return READMES / "reference" / "source_excerpts.json"


def meta_path() -> Path:
    return APP / "data" / "metacognition.json"


def decisions_path() -> Path:
    return records_dir() / "metacognition" / "decisions.json"


def load_meta() -> dict:
    return json.loads(meta_path().read_text(encoding="utf-8"))


def enrich(view: dict, sources: dict) -> dict:
    view["signal"] = signal_summary(records_dir(), sources)
    view["lesson_reason"] = lesson_pick_reason(sources)
    return view


def state_path(day) -> Path:
    return day_os_dir() / f"{day.isoformat()}.json"


def inside(root: Path, target: Path) -> bool:
    root = root.resolve()
    target = target.resolve()
    return target == root or root in target.parents


class CockpitHandler(BaseHTTPRequestHandler):
    server_version = "HelixMatrix/1.0"

    def log_message(self, fmt: str, *args) -> None:
        try:
            sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))
        except (BrokenPipeError, OSError):
            # A detached shell may close its output socket. Logging must never
            # break the response the caller is waiting for.
            pass

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise ValueError("body must be under 16 KB")
        raw = self.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("body must be an object")
        return data

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/day":
            self._day(parse_qs(parsed.query))
            return
        if parsed.path == "/api/project":
            self._project(parse_qs(parsed.query))
            return
        if parsed.path == "/api/meta":
            data = load_meta()
            decisions_file = decisions_path()
            data["decisions"] = (
                json.loads(decisions_file.read_text(encoding="utf-8")).get("decisions", [])
                if decisions_file.is_file() else []
            )
            self._json(200, data)
            return
        if parsed.path == "/api/files":
            self._files(parse_qs(parsed.query))
            return
        if parsed.path == "/api/week":
            self._week()
            return
        if parsed.path == "/api/competence":
            self._competence()
            return
        if parsed.path == "/api/review":
            self._review_read(parse_qs(parsed.query))
            return
        if parsed.path == "/api/german":
            data = read_sources(READMES, REMOTE)["german"]
            data["live"] = self._loopback_live("http://127.0.0.1:8766/api/health")
            self._json(200, data)
            return
        if parsed.path == "/api/export":
            self._export()
            return
        if parsed.path == "/api/monthly":
            self._json(200, monthly_reviews(records_dir()))
            return
        if parsed.path == "/api/n8n":
            self._n8n()
            return
        if parsed.path in {"/", "/index.html", "/Operations___AI_Glossary_Reference_Matrix.html"}:
            self._file(INDEX_PAGE)
            return
        if parsed.path.startswith("/record/"):
            self._record_form(parsed.path[len("/record/"):])
            return
        if parsed.path.startswith("/file/"):
            self._readable_file(parsed.path[len("/file/"):])
            return
        if parsed.path.startswith("/note/"):
            self._note_form(parsed.path[len("/note/"):])
            return
        if parsed.path.startswith("/project/"):
            self._project_files(parsed.path[len("/project/"):])
            return
        self._static(parsed.path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/record":
            self._record_save()
            return
        if path == "/api/approve":
            self._approve()
            return
        if path == "/api/quiz":
            self._quiz()
            return
        if path == "/api/term":
            self._term()
            return
        if path == "/api/review":
            self._review_save()
            return
        if path == "/api/import/validate":
            self._import_validate()
            return
        if path == "/api/import":
            self._import_apply()
            return
        if path == "/api/note":
            self._note_save()
            return
        if path != "/api/tasks":
            self._json(404, {"error": "not found"})
            return
        try:
            payload = self._read_json()
            today = datetime.now(CAIRO).date()
            sources = read_sources(READMES, REMOTE)
            path = state_path(today)
            state = load_state(path, today)
            state = apply_op(state, today, sources, str(payload.get("op", "")), payload, datetime.now(CAIRO))
            save_state(path, state)
            now = clock_in(datetime.now(CAIRO))
            self._json(200, enrich(assemble_day(today, sources, state, now, day_os_dir=day_os_dir()), sources))
        except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _day(self, query: dict) -> None:
        try:
            today = datetime.now(CAIRO).date()
            if "date" in query:
                today = datetime.strptime(query["date"][0], "%Y-%m-%d").date()
            sources = read_sources(READMES, REMOTE)
            state = load_state(state_path(today), today)
            now = clock_in(datetime.now(CAIRO))
            self._json(200, enrich(assemble_day(today, sources, state, now, day_os_dir=day_os_dir()), sources))
        except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            self._json(503, {"error": str(exc), "live": False})

    def _project(self, query: dict) -> None:
        name = (query.get("name") or [""])[0]
        if not name or "/" in name or "\\" in name or name.startswith("."):
            self._json(400, {"error": "bad project name"})
            return
        try:
            projects = {item["folder"]: item for item in read_sources(READMES, REMOTE)["projects"]}
        except (ValueError, FileNotFoundError, OSError) as exc:
            self._json(503, {"error": str(exc), "live": False})
            return
        project = projects.get(name)
        if project is None:
            self._json(404, {"error": "project not in remotely-active"})
            return
        self._json(200, project)

    def _readable_file(self, relative: str) -> None:
        """Read-only view of a known plain-text project file for the chatbot."""
        parts = [part for part in relative.split("/") if part]
        if not parts or ".." in parts or any(part.startswith(".") for part in parts):
            self._json(404, {"error": "not found"})
            return
        target = READMES.joinpath(*parts).resolve()
        if not inside(READMES, target) or not target.is_file():
            self._json(404, {"error": "not found"})
            return
        if target.suffix.lower() not in {".md", ".html", ".txt", ".json"}:
            self._json(403, {"error": "type not served"})
            return
        self._file(target)

    def _files(self, query: dict) -> None:
        term = " ".join((query.get("q") or [""])[0].split()).lower()
        files = load_meta().get("files", [])
        if term:
            words = [word for word in term.split() if word]
            files = [
                item
                for item in files
                if all(
                    word in (item["path"] + " " + item["what"]).lower()
                    for word in words
                )
            ]
        self._json(200, {"files": files, "count": len(files)})

    def _week(self) -> None:
        try:
            sources = read_sources(READMES, REMOTE)
            today = datetime.now(CAIRO).date()
            days = []
            for offset in range(7):
                day = today + timedelta(days=offset)
                tasks = generate_tasks(day, sources)
                lessons = [task for task in tasks if task["kind"] == "learn"]
                days.append(
                    {
                        "date": day.isoformat(),
                        "label": day.strftime("%a"),
                        "short": day.strftime("%d %b"),
                        "lesson": lessons[0]["detail"] if lessons else "",
                        "task_count": len(tasks),
                        "prayers": prayer_times(day) if offset == 0 else None,
                    }
                )
            self._json(200, {"days": days, "today": today.isoformat()})
        except (ValueError, FileNotFoundError, OSError) as exc:
            self._json(503, {"error": str(exc)})

    def _approve(self) -> None:
        try:
            payload = self._read_json()
            choice_id = str(payload.get("id", "")).strip()
            meta = load_meta()
            rec = next(
                (item for item in meta.get("recommendations", []) if item["id"] == choice_id),
                None,
            )
            if rec is None:
                raise ValueError("unknown recommendation")
            note = " ".join(str(payload.get("note", "")).split())[:400]
            path = decisions_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {"version": 1, "decisions": []}
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
            now = datetime.now(CAIRO).isoformat(timespec="minutes")
            data["decisions"] = [
                item for item in data.get("decisions", []) if item.get("id") != choice_id
            ]
            data["decisions"].append(
                {
                    "id": choice_id,
                    "title": rec["title"],
                    "why": rec["why"],
                    "note": note,
                    "approved_at": now,
                }
            )
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            temporary.replace(path)
            self._json(
                200,
                {"ok": True, "approved": choice_id, "count": len(data["decisions"])},
            )
        except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _quiz(self) -> None:
        try:
            payload = self._read_json()
            attempts = record_quiz(
                records_dir(),
                str(payload.get("lesson", "")),
                str(payload.get("question", "")),
                bool(payload.get("correct")),
                datetime.now(CAIRO),
            )
            self._json(200, {"ok": True, "attempts": len(attempts)})
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _term(self) -> None:
        try:
            payload = self._read_json()
            row = grade_term(
                records_dir(),
                str(payload.get("term", "")),
                str(payload.get("grade", "")),
                datetime.now(CAIRO),
            )
            sources = read_sources(READMES, REMOTE)
            due = [item["term"] for item in due_terms(datetime.now(CAIRO).date(), sources)]
            self._json(200, {"ok": True, "grade": row, "due": due})
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _competence(self) -> None:
        try:
            self._json(200, competence_map(records_dir(), read_sources(READMES, REMOTE)))
        except (ValueError, FileNotFoundError, OSError) as exc:
            self._json(503, {"error": str(exc)})

    def _week_day(self, query: dict) -> date:
        value = (query.get("date") or [""])[0]
        return datetime.strptime(value, "%Y-%m-%d").date() if value else datetime.now(CAIRO).date()

    def _review_read(self, query: dict) -> None:
        try:
            day = self._week_day(query)
            path = review_path(records_dir(), day)
            self._json(
                200,
                {
                    "week": iso_week(day),
                    "saved": path.read_text(encoding="utf-8") if path.is_file() else None,
                },
            )
        except ValueError as exc:
            self._json(400, {"error": str(exc)})

    def _review_save(self) -> None:
        try:
            payload = self._read_json()
            day = datetime.now(CAIRO).date()
            if payload.get("date"):
                day = datetime.strptime(str(payload["date"]), "%Y-%m-%d").date()
            path = build_week_review(
                records_dir(), day, read_sources(READMES, REMOTE),
                str(payload.get("note", "")), str(payload.get("focus", "")),
            )
            self._json(200, {"ok": True, "week": iso_week(day), "path": path.name})
        except (ValueError, FileNotFoundError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _project_files(self, rest: str) -> None:
        """Read-only view of the real project folder a task points at."""
        parts = [part for part in rest.split("/") if part]
        if not parts or ".." in parts:
            self._json(404, {"error": "not found"})
            return
        name = parts[0]
        if name.startswith(".") or "\\" in name:
            self._json(404, {"error": "not found"})
            return
        folder = REMOTE / name
        if not folder.is_dir() or not inside(REMOTE, folder):
            self._json(404, {"error": "project not in remotely-active"})
            return
        allowed = {".md", ".txt", ".json", ".yaml", ".yml", ".html"}
        if len(parts) == 1:
            files = sorted(
                path for path in folder.iterdir()
                if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in allowed
            )
            listing = "".join(
                '<li><a href="/project/' + html.escape(name) + "/" + html.escape(item.name) + '">' +
                html.escape(item.name) + "</a></li>" for item in files
            ) or "<li>No readable status or README file in this folder — the gap is real.</li>"
            page = (
                '<!DOCTYPE html><html><body><p><a href="/">← Back to the matrix</a></p>' +
                "<h1>" + html.escape(name) + "</h1><p>Files in the real project folder:</p><ul>" +
                listing + "</ul></body></html>"
            )
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        filename = parts[-1]
        if filename.startswith(".") or ".." in filename or "/" in filename:
            self._json(404, {"error": "not found"})
            return
        target = (folder / filename).resolve()
        if not inside(folder, target) or not target.is_file() or target.suffix.lower() not in allowed:
            self._json(404, {"error": "file not readable"})
            return
        self._send(200, target.read_bytes(), "text/plain; charset=utf-8")

    def _note_day(self, value: str) -> date:
        return datetime.strptime(value, "%Y-%m-%d").date()

    def _note_form(self, value: str) -> None:
        try:
            day = self._note_day(value)
        except ValueError:
            self._json(400, {"error": "bad date"})
            return
        esc = html.escape
        current = read_note(records_dir(), day)
        page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Today's note — {esc(day.isoformat())}</title>
<style>body{{font-family:'IBM Plex Sans',system-ui,sans-serif;max-width:44rem;margin:2rem auto;padding:0 1rem;line-height:1.6}}
textarea{{width:100%;min-height:10rem;font:inherit;padding:.7rem;border:1px solid #8d8d8d;background:#fff;color:#161616}}
button{{font:inherit;padding:.6rem 1.1rem;background:#0f62fe;color:#fff;border:0;cursor:pointer}}
a{{color:#0f62fe}}.ref{{color:#525252;font-size:.85rem}}</style></head><body>
<p><a href="/">← Back to the matrix</a></p>
<h1>Today's note — {esc(day.isoformat())}</h1>
<p class="ref">This is the "today's note" the project task refers to. Copy a project's real status line here — or, if there is none, write that the gap is open. Do not invent a status.</p>
<form method="post" action="/api/note">
<input type="hidden" name="date" value="{esc(day.isoformat())}">
<textarea name="text" required minlength="10" maxlength="8000" autofocus>{esc(current)}</textarea>
<p><button type="submit">Save today's note</button></p>
</form>
</body></html>"""
        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def _note_save(self) -> None:
        esc = html.escape
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 20_000:
                raise ValueError("note must be under 20 KB")
            form = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            day = self._note_day((form.get("date") or [""])[0])
            path = save_note(records_dir(), day, (form.get("text") or [""])[0])
            page = (
                "<!DOCTYPE html><html><body><p><strong>Saved.</strong> Today's note is a learning record at " +
                esc(path.name) + ".</p><p><a href='/'>← Back to the matrix</a></p></body></html>"
            )
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        except (ValueError, OSError) as exc:
            page = "<!DOCTYPE html><html><body><h1>Could not save</h1><p>" + esc(str(exc)) + \
                '</p><p><a href="javascript:history.back()">Go back</a></p></body></html>'
            self._send(400, page.encode("utf-8"), "text/html; charset=utf-8")

    @staticmethod
    def _loopback_live(url: str) -> bool:
        try:
            with urlopen(url, timeout=2) as response:
                return response.status == 200
        except OSError:
            return False

    def _n8n(self) -> None:
        live, detail = False, "not reachable"
        try:
            with urlopen("http://127.0.0.1:5678/healthz", timeout=2) as response:
                if response.status == 200:
                    live = True
                    detail = response.read(200).decode("utf-8", errors="replace").strip()
        except OSError as exc:
            detail = str(exc)
        self._json(
            200,
            {
                "live": live,
                "detail": detail,
                "url": "http://127.0.0.1:5678/",
                "status": "88% · deployed, not client-ready",
                "verified": "Compose starts postgres and n8n healthy; backup restored into a disposable stack; Ollama 0.40.16 on ROCm verified 100% on GPU.",
                "blockers": [
                    "Cloudflare Tunnel token and public hostname",
                    "Cloudflare Access with MFA",
                    "Public webhook test",
                    "Trivy image scan and host reinstall",
                ],
                "host": "Ubuntu 26.04 · RX 6700 XT · 16 vCPU",
                "repository": "3 commits, 58 tracked files, clean tree, no remote · archive Career/n8n-production-repo.tar",
            },
        )

    def _export(self) -> None:
        payload = export_history(records_dir(), datetime.now(CAIRO))
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header(
            "Content-Disposition",
            'attachment; filename="helix-matrix-history-' + datetime.now(CAIRO).strftime("%Y-%m-%d") + '.json"',
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _import_validate(self) -> None:
        try:
            payload = self._read_json()
            self._json(200, validate_import(payload))
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

    def _import_apply(self) -> None:
        try:
            payload = self._read_json()
            written = import_history(records_dir(), payload)
            self._json(200, {"ok": True, "written": written, "count": len(written)})
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _record_form(self, filename: str) -> None:
        try:
            detail = lesson_detail(READMES / "lessons", filename)
        except (ValueError, FileNotFoundError) as exc:
            self._send(
                404,
                ("<h1>Lesson not found</h1><p>" + html.escape(str(exc)) + "</p>").encode("utf-8"),
                "text/html; charset=utf-8",
            )
            return
        prompt = detail["prompt"] or (
            "Write one sentence in your own words about what this lesson taught you."
        )
        esc = html.escape
        page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Write your answer — {esc(detail['title'])}</title>
<style>
body{{font-family:'IBM Plex Sans',system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#161616;line-height:1.6}}
h1{{font-size:1.5rem}} .ref{{color:#525252;font-size:.85rem}}
article{{border:1px solid #e0e0e0;border-left:3px solid #0f62fe;padding:1rem;margin:1rem 0;background:#f4f4f4}}
textarea{{width:100%;min-height:9rem;font:inherit;padding:.75rem;border:1px solid #8d8d8d;background:#fff}}
button{{font:inherit;padding:.6rem 1.2rem;background:#0f62fe;color:#fff;border:0;cursor:pointer}}
button:disabled{{opacity:.5;cursor:not-allowed}}
a{{color:#0f62fe}}
</style></head><body>
<p><a href="/">← Back to the matrix</a> · <a href="/lessons/{esc(filename)}">Open the lesson</a></p>
<h1>Write your final answer</h1>
<p class="ref">{esc(detail['title'])} · saved as a learning record, then reflected on the matrix.</p>
<form method="post" action="/api/record" id="answer-form" novalidate>
<input type="hidden" name="lesson" value="{esc(filename)}">
<p class="ref">Step 1 of 2 — retrieval, before you look at the task.</p>
<label for="retrieval"><strong>Two lines from memory</strong></label><br>
<textarea id="retrieval" name="retrieval" required rows="3" maxlength="2000" autofocus
  placeholder="What do I already know about this?&#10;What would I say without re-reading?"></textarea>
<p class="ref" id="retrieval-note">Two separate lines, at least 40 characters in total.</p>
<p class="ref">Step 2 of 2 — your final answer.</p>
<article><strong>Your task</strong><p>{esc(prompt)}</p></article>
<label for="answer"><strong>My answer (in my own words):</strong></label><br>
<textarea id="answer" name="answer" required minlength="20" maxlength="8000"></textarea>
<p><button type="submit" id="save-answer">Save answer &amp; mark done</button></p>
<p class="ref" id="save-note">Two retrieval lines and one full answer are required; Save will tell you what is missing.</p>
</form>
<script>
(function(){{var r=document.getElementById('retrieval'),a=document.getElementById('answer'),
form=document.getElementById('answer-form'),rn=document.getElementById('retrieval-note'),sn=document.getElementById('save-note'),
okR=false,okA=false;
function check(){{var lines=r.value.split('\\n').map(function(x){{return x.trim();}}).filter(Boolean);
okR=lines.length>=2 && lines.join('').length>=40;okA=a.value.trim().length>=20;
rn.textContent=okR?'Retrieval captured.':'Two separate lines, at least 40 characters in total.';
sn.textContent=!okR?'Step 1: write two lines from memory before saving.':(!okA?'Step 2: write your final answer (one full sentence).':'Ready — press Save answer & mark done.');}}
form.addEventListener('submit',function(e){{check();if(!(okR&&okA)){{e.preventDefault();sn.textContent=!okR?'Not saved: write two retrieval lines first (Step 1).':'Not saved: write your final answer first (Step 2).';(!okR?r:a).focus();}}}});
r.addEventListener('input',check);a.addEventListener('input',check);check();}})();
</script>
</body></html>"""
        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def _record_save(self) -> None:
        esc = html.escape
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                raise ValueError("form body must be under 16 KB")
            form = parse_qs(
                self.rfile.read(length).decode("utf-8"), keep_blank_values=True
            )
            filename = (form.get("lesson") or [""])[0]
            answer = (form.get("answer") or [""])[0]
            retrieval = (form.get("retrieval") or [""])[0]
            if not valid_retrieval(retrieval):
                raise ValueError("write two lines from memory before the answer")
            if (
                "/" in filename
                or "\\" in filename
                or ".." in filename
                or not filename.endswith(".html")
            ):
                raise ValueError("bad lesson name")
            now = datetime.now(CAIRO)
            sources = read_sources(READMES, REMOTE)
            lesson = next(
                (item for item in sources["lessons"] if item["file"] == filename), None
            )
            if lesson is None:
                raise ValueError("lesson is not in the index")
            path = write_answer(records_dir(), lesson, answer, now, retrieval)

            today = now.date()
            current = state_path(today)
            state = load_state(current, today)
            view = assemble_day(today, sources, state, clock_in(now))
            task_id = next(
                (
                    item["id"]
                    for item in view["tasks"]
                    if (item.get("links") or {}).get("lesson") == filename
                ),
                None,
            )
            if task_id:
                state = apply_op(
                    state, today, sources, "check", {"id": task_id}, now
                )
                save_state(current, state)

            fresh = read_sources(READMES, REMOTE)
            done = sum(1 for item in fresh["lessons"] if item["recorded"])
            page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Answer saved — {esc(lesson['title'])}</title>
<style>body{{font-family:'IBM Plex Sans',system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;line-height:1.6}}
.box{{border:1px solid #defbe6;border-left:3px solid #198038;background:#defbe6;padding:1rem}}
a{{color:#0f62fe}}</style></head><body>
<div class="box"><strong>Saved.</strong> Your answer is a learning record and this lesson is marked done.
{done} of {len(fresh['lessons'])} lessons now recorded.</div>
<p><a href="/">← Back to the matrix (progress updated)</a> ·
<a href="/lessons/{esc(filename)}">Re-open the lesson</a></p>
<p class="ref">Stored at learning-records/{esc(path.name)}</p>
</body></html>"""
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            page = (
                "<!DOCTYPE html><html><body><h1>Could not save</h1><p>"
                + esc(str(exc))
                + '</p><p><a href="javascript:history.back()">Go back</a></p></body></html>'
            )
            self._send(400, page.encode("utf-8"), "text/html; charset=utf-8")

    def _static(self, path: str) -> None:
        parts = [part for part in path.split("/") if part]
        if not parts or ".." in parts:
            self._json(404, {"error": "not found"})
            return
        root = STATIC_ROOTS.get(parts[0])
        if root is None:
            self._json(404, {"error": "not found"})
            return
        target = root.joinpath(*parts[1:]).resolve()
        if not inside(root, target) or not target.is_file():
            self._json(404, {"error": "not found"})
            return
        if target.suffix.lower() not in ALLOWED_SUFFIXES:
            self._json(403, {"error": "type not served"})
            return
        if root == STATIC_ROOTS["lessons"] and target.suffix.lower() == ".html":
            self._lesson(target)
            return
        self._file(target)

    def _lesson(self, path: Path) -> None:
        """Serve a lesson with a live 'write your answer' link injected."""
        body = path.read_text(encoding="utf-8", errors="replace")
        source_block = ""
        try:
            excerpts = json.loads(excerpts_path().read_text(encoding="utf-8"))
            item = excerpts.get("lessons", {}).get(path.name[:4])
            if item:
                url = html.escape(item.get("url", ""))
                link = (
                    ' <a href="' + url + '" target="_blank" rel="noopener">Verify at source ↗</a>'
                    if url else " (no external source recorded — gap left open)"
                )
                source_block = (
                    '<div data-no-speak style="border:1px solid #4fd1a1;border-left:3px solid #4fd1a1;'
                    'background:#10352a;padding:.8rem;margin:1.2rem 0 0">'
                    "<strong>Source note</strong> · " + html.escape(item.get("note", "")) + link +
                    "<br><small>" + html.escape(item.get("source", "")) +
                    " · curated note in local source_excerpts.json, not a verbatim quote.</small></div>"
                )
        except (ValueError, OSError):
            source_block = ""
        banner = (
            '<div data-no-speak style="border:1px solid #0f62fe;border-left:3px solid #0f62fe;'
            'background:#d0e2ff;padding:.8rem;margin:1.2rem 0">'
            '<strong>Done with the homework?</strong> '
            '<a href="/record/'
            + html.escape(path.name)
            + '">Write your final answer →</a> '
            '— saved as a learning record and marked done on the matrix.'
            "</div>"
        )
        quiz_script = (
            "<script>(function(){var lesson=" + json.dumps(path.name) + ";"
            "document.addEventListener('click',function(e){"
            "var b=e.target&&e.target.closest?e.target.closest('button'):null;"
            "if(!b)return;var oc=b.getAttribute('onclick')||'';"
            "var m=oc.match(/ans\\(['\"]([^'\"]+)['\"]\\s*,\\s*\\d+\\s*,\\s*(true|false)\\)/);"
            "if(!m)return;fetch('/api/quiz',{method:'POST',headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({lesson:lesson,question:m[1],correct:m[2]==='true'})});"
            "});})();</script>"
        )
        voice_script = r"""<script>
(function(){
  var bar=document.createElement('div');
  bar.setAttribute('data-no-speak','');
  bar.style.cssText='border:1px solid #62d0d8;border-left:3px solid #62d0d8;background:#10352a;padding:.7rem;margin:1.2rem 0;display:flex;gap:.5rem;flex-wrap:wrap;align-items:center';
  bar.innerHTML='<strong>Listen to this lesson</strong><button type="button" id="lesson-speak">▶ Speak</button><button type="button" id="lesson-stop">■ Stop</button><span style="font-size:.75rem;opacity:.8">Local speech — nothing leaves this device.</span>';
  var heading=document.querySelector('h1');
  if(heading&&heading.parentNode) heading.parentNode.insertBefore(bar,heading.nextSibling);
  function pickVoice(lang){var vs=window.speechSynthesis?window.speechSynthesis.getVoices():[];for(var i=0;i<vs.length;i++){if(vs[i].lang.toLowerCase().indexOf(lang)===0)return vs[i];}return null;}
  function isGerman(t){return /[äöüßÄÖÜ]|\b(und|der|die|das|ist|nicht|mit|für|sich|auf|eine|werden)\b/i.test(t);}
  function speak(){
    if(!('speechSynthesis' in window)){document.getElementById('lesson-speak').textContent='Speech not supported';return;}
    window.speechSynthesis.cancel();
    var nodes=Array.prototype.slice.call(document.querySelectorAll('h1,h2,p,li,td'));
    var parts=nodes.filter(function(el){return !el.closest('[data-no-speak]')&&!el.closest('.quiz')&&!el.closest('script');})
      .map(function(el){return (el.textContent||'').trim().replace(/\s+/g,' ');})
      .filter(function(t){return t.length>2;});
    parts.forEach(function(text){var u=new SpeechSynthesisUtterance(text);var de=isGerman(text);var v=pickVoice(de?'de':'en');if(v)u.voice=v;u.lang=de?'de-DE':'en-US';u.rate=.95;window.speechSynthesis.speak(u);});
  }
  document.getElementById('lesson-speak').addEventListener('click',speak);
  document.getElementById('lesson-stop').addEventListener('click',function(){window.speechSynthesis.cancel();});
})();
</script>"""
        if "</body>" in body.lower():
            index = body.lower().rfind("</body>")
            body = body[:index] + source_block + banner + quiz_script + voice_script + body[index:]
        else:
            body += banner
        self._send(200, body.encode("utf-8"), "text/html; charset=utf-8")

    def _file(self, path: Path) -> None:
        types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".md": "text/plain; charset=utf-8",
            ".svg": "image/svg+xml",
        }
        body = path.read_bytes()
        self._send(200, body, types.get(path.suffix.lower(), "application/octet-stream"))


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), CockpitHandler)
    print(f"Helix-Matrix on http://{HOST}:{PORT}/", flush=True)
    print(f"readmes {READMES}", flush=True)
    print(f"remote  {REMOTE}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
