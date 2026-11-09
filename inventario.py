"""Inventario local de metadatos, persistente y reanudable para el primer mapa."""
from __future__ import annotations

import ctypes
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "JardinZen"
DB_FILE = STATE_DIR / "inventario.sqlite3"
_lock = threading.Lock()
_thread: threading.Thread | None = None
_pause = threading.Event()
_stop = threading.Event()


def fixed_roots() -> list[str]:
    """Unidades locales fijas visibles ahora; excluye volúmenes de nube y red."""
    if os.name != "nt":
        return [str(Path.home())]
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    get_type = ctypes.windll.kernel32.GetDriveTypeW
    roots = []
    get_volume = ctypes.windll.kernel32.GetVolumeInformationW
    for i in range(26):
        root = f"{chr(65+i)}:\\"
        if not (mask & (1 << i)) or get_type(ctypes.c_wchar_p(root)) != 3:
            continue
        label = ctypes.create_unicode_buffer(261)
        if get_volume(ctypes.c_wchar_p(root), label, len(label), None, None, None, None, 0):
            description = label.value.casefold()
            if any(token in description for token in ("google", "onedrive", "dropbox", "icloud", "@")):
                continue
        roots.append(root)
    return roots


def connect() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_FILE, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA busy_timeout=30000")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS runs(
        id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        finished_at TEXT, status TEXT NOT NULL, roots TEXT NOT NULL,
        item_count INTEGER NOT NULL DEFAULT 0, dirs_done INTEGER NOT NULL DEFAULT 0,
        errors INTEGER NOT NULL DEFAULT 0, skipped_reparse INTEGER NOT NULL DEFAULT 0,
        note TEXT);
      CREATE TABLE IF NOT EXISTS items(
        path TEXT PRIMARY KEY COLLATE NOCASE, root TEXT NOT NULL, parent TEXT,
        name TEXT NOT NULL, kind TEXT NOT NULL, extension TEXT,
        size INTEGER, created REAL, modified REAL, attributes INTEGER,
        first_seen TEXT NOT NULL, last_seen TEXT NOT NULL);
      CREATE INDEX IF NOT EXISTS items_parent ON items(parent);
      CREATE INDEX IF NOT EXISTS items_root ON items(root);
      CREATE TABLE IF NOT EXISTS directories(
        path TEXT PRIMARY KEY COLLATE NOCASE, root TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT);
      CREATE INDEX IF NOT EXISTS dirs_status ON directories(status);
      CREATE TABLE IF NOT EXISTS scan_errors(
        id INTEGER PRIMARY KEY, at TEXT NOT NULL, path TEXT NOT NULL, error TEXT NOT NULL);
    """)
    return db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_or_resume(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT id,status FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    if row and row[1] in ("running", "paused", "stopped", "interrupted"):
        roots = fixed_roots()
        excluded = db.execute("SELECT DISTINCT root FROM directories WHERE root NOT IN (%s)" %
                              ",".join("?" for _ in roots), roots).fetchall() if roots else []
        excluded_roots = [x[0] for x in excluded]
        db.execute("UPDATE runs SET status='running',updated_at=?,finished_at=NULL,roots=?,note=? WHERE id=?",
                   (_now(), json.dumps(roots), "Unidades virtuales omitidas: " + ", ".join(r[:2] for r in excluded_roots) if excluded_roots else None, row[0]))
        if excluded_roots:
            db.executemany("UPDATE directories SET status='excluded' WHERE root=? AND status IN ('pending','processing')",
                           [(r,) for r in excluded_roots])
        if roots:
            db.execute("UPDATE directories SET status='pending' WHERE status='processing' AND root IN (%s)" %
                       ",".join("?" for _ in roots), roots)
        db.commit()
        return row[0]
    if row and row[1] in ("complete", "complete_with_errors"):
        return row[0]
    roots = fixed_roots()
    if not roots:
        raise RuntimeError("No se encontraron unidades locales fijas con letra.")
    now = _now()
    cur = db.execute("INSERT INTO runs(started_at,updated_at,status,roots) VALUES(?,?,?,?)",
                     (now, now, "running", json.dumps(roots)))
    for root in roots:
        db.execute("INSERT OR IGNORE INTO directories(path,root,status) VALUES(?,?, 'pending')", (root, root))
    db.commit()
    return int(cur.lastrowid)


def start() -> dict:
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return status()
        _pause.clear()
        _stop.clear()
        db = connect()
        run_id = _new_or_resume(db)
        db.close()
        row = status()
        if row.get("status") in ("complete", "complete_with_errors"):
            return row
        _thread = threading.Thread(target=_worker, args=(run_id,), name="JardineroInventario", daemon=True)
        _thread.start()
    return status()


def pause() -> dict:
    _pause.set()
    return status()


def resume() -> dict:
    _pause.clear()
    return start()


def stop() -> dict:
    _stop.set()
    _pause.clear()
    return status()


def status() -> dict:
    if not DB_FILE.exists():
        return {"available": True, "status": "not_started", "items": 0, "directories_done": 0,
                "directories_pending": 0, "errors": 0, "skipped_reparse": 0, "roots": []}
    try:
        db = sqlite3.connect(f"file:{DB_FILE.as_posix()}?mode=ro", uri=True, timeout=2)
        row = db.execute("SELECT id,started_at,updated_at,finished_at,status,roots,item_count,dirs_done,errors,skipped_reparse,note FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            db.close()
            return {"available": True, "status": "not_started", "items": 0, "directories_done": 0,
                    "directories_pending": 0, "errors": 0, "skipped_reparse": 0, "roots": []}
        pending = db.execute("SELECT count(*) FROM directories WHERE status='pending'").fetchone()[0]
        excluded = db.execute("SELECT count(*) FROM directories WHERE status='excluded'").fetchone()[0]
        db.close()
        worker_alive = bool(_thread and _thread.is_alive())
        visible_status = "interrupted" if row[4] == "running" and not worker_alive else row[4]
        return {"available": True, "run_id": row[0], "started_at": row[1], "updated_at": row[2],
                "finished_at": row[3], "status": visible_status, "roots": json.loads(row[5]), "items": row[6],
                "directories_done": row[7], "errors": row[8], "skipped_reparse": row[9],
                "note": row[10], "directories_pending": pending,
                "directories_excluded": excluded,
                "worker_alive": worker_alive}
    except (sqlite3.Error, OSError, ValueError) as exc:
        return {"available": False, "status": "error", "error": str(exc)}


def _record_error(db: sqlite3.Connection, run_id: int, path: str, error: str) -> None:
    db.execute("INSERT INTO scan_errors(at,path,error) VALUES(?,?,?)", (_now(), path, error[:1000]))
    db.execute("UPDATE runs SET errors=errors+1,updated_at=? WHERE id=?", (_now(), run_id))


def _worker(run_id: int) -> None:
    db = connect()
    roots_row = db.execute("SELECT roots FROM runs WHERE id=?", (run_id,)).fetchone()
    active_roots = json.loads(roots_row[0]) if roots_row else []
    if active_roots:
        db.execute("UPDATE directories SET status='pending' WHERE status='processing' AND root IN (%s)" %
                   ",".join("?" for _ in active_roots), active_roots)
    db.commit()
    db.execute("UPDATE runs SET status='running',updated_at=? WHERE id=?", (_now(), run_id))
    db.commit()
    last_commit = time.monotonic()
    try:
        while not _stop.is_set():
            if _pause.is_set():
                db.execute("UPDATE runs SET status='paused',updated_at=? WHERE id=?", (_now(), run_id)); db.commit()
                while _pause.is_set() and not _stop.is_set():
                    time.sleep(.5)
                if _stop.is_set(): break
                db.execute("UPDATE runs SET status='running',updated_at=? WHERE id=?", (_now(), run_id)); db.commit()
            row = db.execute("SELECT path,root FROM directories WHERE status='pending' LIMIT 1").fetchone()
            if row is None:
                errors = db.execute("SELECT errors FROM runs WHERE id=?", (run_id,)).fetchone()[0]
                db.execute("UPDATE runs SET status=?,finished_at=?,updated_at=?,note=? WHERE id=?",
                           ("complete_with_errors" if errors else "complete", _now(), _now(),
                            "Inventario terminado con rutas inaccesibles." if errors else "Inventario completo.", run_id))
                db.commit()
                break
            folder, root = row
            db.execute("UPDATE directories SET status='processing',attempts=attempts+1 WHERE path=?", (folder,))
            db.commit()
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if _stop.is_set() or _pause.is_set():
                            break
                        try:
                            info = entry.stat(follow_symlinks=False)
                            created = getattr(info, "st_birthtime", info.st_ctime)
                            attrs = getattr(info, "st_file_attributes", 0)
                            reparse = bool(getattr(info, "st_reparse_tag", 0) or attrs & 0x400)
                            path = entry.path
                            is_dir = entry.is_dir(follow_symlinks=False)
                            now = _now()
                            kind = "link" if reparse else ("directory" if is_dir else "file")
                            inserted = db.execute("""INSERT OR IGNORE INTO items(path,root,parent,name,kind,extension,size,created,modified,attributes,first_seen,last_seen)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                              (path, root, folder, entry.name, kind,
                               "" if is_dir else Path(entry.name).suffix.lower(), None if is_dir else info.st_size,
                               created, info.st_mtime, attrs, now, now))
                            if inserted.rowcount:
                                db.execute("UPDATE runs SET item_count=item_count+1 WHERE id=?", (run_id,))
                            else:
                                db.execute("UPDATE items SET size=?,created=?,modified=?,attributes=?,last_seen=? WHERE path=?",
                                           (None if is_dir else info.st_size, created, info.st_mtime, attrs, now, path))
                            if is_dir and not reparse:
                                db.execute("INSERT OR IGNORE INTO directories(path,root,status) VALUES(?,?, 'pending')", (path, root))
                            elif reparse and inserted.rowcount:
                                db.execute("UPDATE runs SET skipped_reparse=skipped_reparse+1 WHERE id=?", (run_id,))
                        except OSError as exc:
                            _record_error(db, run_id, entry.path, f"{type(exc).__name__}: {exc}")
                        if time.monotonic() - last_commit >= 2:
                            db.execute("UPDATE runs SET updated_at=? WHERE id=?", (_now(), run_id)); db.commit(); last_commit = time.monotonic()
                if _stop.is_set() or _pause.is_set():
                    db.execute("UPDATE directories SET status='pending' WHERE path=?", (folder,))
                else:
                    db.execute("UPDATE directories SET status='done',last_error=NULL WHERE path=?", (folder,))
                    db.execute("UPDATE runs SET dirs_done=dirs_done+1 WHERE id=?", (run_id,))
            except OSError as exc:
                db.execute("UPDATE directories SET status='error',last_error=? WHERE path=?", (str(exc)[:1000], folder))
                _record_error(db, run_id, folder, f"{type(exc).__name__}: {exc}")
            db.execute("UPDATE runs SET updated_at=? WHERE id=?", (_now(), run_id)); db.commit(); last_commit = time.monotonic()
        if _stop.is_set():
            db.execute("UPDATE runs SET status='stopped',updated_at=? WHERE id=?", (_now(), run_id)); db.commit()
    except Exception as exc:
        db.execute("UPDATE runs SET status='interrupted',note=?,updated_at=? WHERE id=?", (f"{type(exc).__name__}: {exc}"[:1000], _now(), run_id))
        db.commit()
    finally:
        db.close()
