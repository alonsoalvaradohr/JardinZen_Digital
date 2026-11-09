#!/usr/bin/env python3
"""Visor web local, de solo lectura, para el estado real de Jardinero."""
from __future__ import annotations

import json
import os
import subprocess
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import inventario
import proyectos
import propuestas
import brain

HOST = "127.0.0.1"
PORT = int(os.environ.get("JARDINERO_VIEWER_PORT", "8765"))
HERE = Path(__file__).resolve().parent
HTML = HERE / "visor.html"
STATE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "JardinZen"
RUNTIME_FILE = STATE_DIR / "runtime.json"
DB_FILE = STATE_DIR / "index.sqlite3"
STATE_JSON = STATE_DIR / "STATE.json"
_task_cache = {"at": 0.0, "value": {"registered": False}}


def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return fallback


def ollama_health():
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as response:
            payload = json.load(response)
        return {"online": True, "models": [m.get("name", "") for m in payload.get("models", [])]}
    except (OSError, ValueError, TimeoutError):
        return {"online": False, "models": []}


def task_health():
    """Consulta el Programador de Windows; salida cacheada para no sondearlo cada segundo."""
    now = time.monotonic()
    if now - _task_cache["at"] < 30:
        return _task_cache["value"]
    command = ("$t=Get-ScheduledTask -TaskName 'JardinZen_Jardinero' -ErrorAction Stop; "
               "$i=Get-ScheduledTaskInfo -TaskName 'JardinZen_Jardinero'; "
               "[ordered]@{registered=$true;state=[string]$t.State;lastRun=$i.LastRunTime.ToString('o');"
               "nextRun=$i.NextRunTime.ToString('o');lastResult=$i.LastTaskResult} | ConvertTo-Json -Compress")
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                                capture_output=True, text=True, timeout=4, check=False)
        value = json.loads(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else {"registered": False}
    except (OSError, subprocess.TimeoutExpired, ValueError):
        value = {"registered": False}
    _task_cache.update(at=now, value=value)
    return value


def pot_items(roots):
    pots = []
    for index, raw in enumerate(roots):
        path = Path(raw)
        try:
            items = sorted(path.iterdir(), key=lambda p: p.name.lower()) if path.is_dir() else []
        except OSError:
            items = []
        visible = [p for p in items if not p.name.startswith(".")]
        pots.append({
            "label": "Maceta de Descargas" if index == 0 else "Maceta del Escritorio" if index == 1 else f"Maceta {index + 1}",
            "path": str(path), "exists": path.is_dir(), "count": len(visible),
            "items": [{"name": p.name, "kind": "carpeta" if p.is_dir() else (p.suffix.lstrip(".").upper() or "ARCHIVO"),
                       "bytes": p.stat().st_size if p.is_file() else 0,
                       "modified": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()}
                      for p in visible[:30] if _stat_ok(p)]
        })
    return pots


def _stat_ok(path):
    try:
        path.stat()
        return True
    except OSError:
        return False


def overview():
    runtime = read_json(RUNTIME_FILE, {})
    state = read_json(STATE_JSON, {})
    run = read_json(STATE_DIR / "RUN.json", {})
    pots = pot_items(runtime.get("pots", []))
    payload = {"ok": True, "app": "JardineroVisor", "state": state,
               "garden_root": runtime.get("garden_root", str(Path.home() / "JardinZen")),
               "pots": pots, "health": {"sqlite": False, "ollama": ollama_health()},
               "task": task_health(), "run": run, "run_events": recent_run_events(),
               "forest": [], "moves": [], "reviews": [], "totals": {"documents": 0, "moves": 0, "chunks": 0,
                   "embeddings": 0, "reviews": 0, "pot_items": sum(p["count"] for p in pots)}}
    payload["inventory"] = inventario.status()
    payload["garden"] = proyectos.overview()
    if not DB_FILE.exists():
        payload["error"] = "Aún no existe el índice local. Ejecuta primero INICIAR.cmd."
        return payload
    try:
        uri = DB_FILE.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=2) as db:
            db.row_factory = sqlite3.Row
            payload["health"]["sqlite"] = db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            totals = db.execute("""SELECT (SELECT count(*) FROM docs) documents,
                (SELECT count(*) FROM moves WHERE status='COMPLETE') moves,
                (SELECT count(*) FROM chunks) chunks,
                (SELECT count(*) FROM chunks WHERE embedding IS NOT NULL) embeddings,
                (SELECT count(*) FROM decisions WHERE status='REVIEW') reviews""").fetchone()
            payload["totals"].update(dict(totals))
            payload["forest"] = [dict(row) for row in db.execute("""SELECT domain, project, count(*) AS documents,
                max(created_at) AS latest FROM docs GROUP BY domain, project ORDER BY domain, project""")]
            payload["moves"] = [dict(row) for row in db.execute("""SELECT src, dest, digest, status, created_at
                FROM moves ORDER BY created_at DESC LIMIT 40""")]
            payload["reviews"] = [dict(row) for row in db.execute("""SELECT src, seen_at FROM decisions
                WHERE status='REVIEW' ORDER BY seen_at DESC LIMIT 40""")]
    except (sqlite3.Error, OSError) as exc:
        payload["error"] = f"No se pudo leer SQLite en modo seguro: {exc}"
    return payload


def recent_run_events(limit=12):
    logs = STATE_DIR / "logs"
    try:
        files = sorted(logs.glob("jardinero-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        events = []
        for path in files:
            raw = path.read_bytes()[-128_000:].decode("utf-8", errors="replace")
            for line in reversed(raw.splitlines()):
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                events.append({k: item[k] for k in ("time", "event", "source", "reason", "error", "confidence", "domain", "project") if k in item})
                if len(events) >= limit:
                    return list(reversed(events))
        return list(reversed(events))
    except OSError:
        return []


class Handler(BaseHTTPRequestHandler):
    server_version = "JardineroVisor/1.2"

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/health":
            self._json({"app": "JardineroVisor", "build": "JZ-019-brain-api-v1",
                        "proposal_build": propuestas.BUILD_ID, "proposal_api": True,
                        "brain_build": brain.BUILD_ID,
                        "host": HOST, "port": PORT})
            return
        if route == "/api/brain/status":
            self._json(brain.status())
            return
        if route == "/api/inventory/status":
            self._json(inventario.status())
            return
        if route == "/api/garden/project":
            from urllib.parse import parse_qs
            path = parse_qs(urlparse(self.path).query).get("path", [""])[0]
            self._json(proyectos.detail(path))
            return
        if route == "/api/proposals/status":
            self._json(propuestas.status())
            return
        if route == "/api/brain/search":
            from urllib.parse import parse_qs
            query = parse_qs(urlparse(self.path).query).get("q", [""])[0]
            self._json(brain.search(query))
            return
        if route == "/api/overview":
            body = json.dumps(overview(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route not in ("/", "/index.html"):
            self.send_error(404)
            return
        try:
            body = HTML.read_bytes()
        except OSError:
            self.send_error(500, "No se encontró visor.html")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/api/brain/ask":
            try:
                length = min(int(self.headers.get("Content-Length", "0")), 4096)
                payload = json.loads(self.rfile.read(length) or b"{}")
                self._json(brain.ask(str(payload.get("query", ""))))
            except Exception as exc:
                self._json({"status": "error", "error": f"{type(exc).__name__}: {exc}"}, 500)
            return
        actions = {"/api/inventory/start": inventario.start,
                   "/api/inventory/pause": inventario.pause,
                   "/api/inventory/resume": inventario.resume,
                   "/api/inventory/stop": inventario.stop,
                   "/api/projects/discover": proyectos.start,
                   "/api/proposals/start": propuestas.start,
                   "/api/proposals/next": propuestas.process,
                   "/api/brain/start": brain.start,
                   "/api/brain/pause": brain.pause,
                   "/api/brain/resume": brain.resume,
                   "/api/brain/stop": brain.stop}
        action = actions.get(route)
        if not action:
            self.send_error(404)
            return
        try:
            self._json(action())
        except Exception as exc:
            self._json({"status": "error", "error": f"{type(exc).__name__}: {exc}"}, 500)

    def _json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {fmt % args}")


def main():
    if not HTML.is_file():
        raise SystemExit(f"Falta la interfaz: {HTML}")
    brain.resume_if_active()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Jardín local listo en http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
