"""Inventario y propuestas contextuales metadata-only para JZ-017.

No recorre el disco ni lee contenido. Consume exclusivamente filas existentes
del mapa local, limitadas a las macetas configuradas en runtime.json.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import inventario

STATE_DIR = inventario.STATE_DIR
DB_FILE = STATE_DIR / "propuestas.sqlite3"
BATCH_SIZE = 30
BUILD_ID = "jz018-paginated-v3"
GENERIC_TOKENS = {"csv", "pdf", "txt", "md", "json", "xml", "yaml", "yml", "xlsx", "xls",
                  "docx", "doc", "pptx", "ppt", "log", "file", "data", "report", "readme",
                  "export", "scan", "sin", "fecha", "system", "audit", "test", "temp",
                  "backup", "copy", "final", "draft", "result", "measurement", "telemetry"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_FILE, timeout=15)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL, status TEXT NOT NULL, roots TEXT NOT NULL,
      cursor TEXT, total INTEGER NOT NULL DEFAULT 0, processed INTEGER NOT NULL DEFAULT 0,
      error TEXT);
    CREATE TABLE IF NOT EXISTS proposals(id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL,
      source TEXT NOT NULL, parent TEXT, name TEXT NOT NULL, extension TEXT, size INTEGER,
      modified REAL, project TEXT, project_path TEXT, evidence TEXT NOT NULL,
      proposed_name TEXT NOT NULL, proposed_destination TEXT, state TEXT NOT NULL,
      created_at TEXT NOT NULL, UNIQUE(job_id, source));
    CREATE INDEX IF NOT EXISTS proposals_job_state ON proposals(job_id,state);
    """)
    return db


def _roots():
    runtime = STATE_DIR / "runtime.json"
    try:
        data = json.loads(runtime.read_text(encoding="utf-8-sig"))
        return [os.path.abspath(os.path.normpath(p)) for p in data.get("pots", [])[:2]]
    except (OSError, ValueError, TypeError):
        return []


def _inside(path, root):
    try:
        return os.path.commonpath([os.path.normcase(path), os.path.normcase(root)]) == os.path.normcase(root)
    except ValueError:
        return False


def _sqlite_nocase_key(value):
    """Mirror SQLite's ASCII NOCASE order for a stable cross-root cursor."""
    return str(value).translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"))


def _pot_file_count(inv, roots):
    total = 0
    for root in roots:
        prefix = root.rstrip("\\/") + os.sep
        total += inv.execute("""SELECT count(*) FROM items WHERE kind='file'
          AND path>=? COLLATE NOCASE AND path<? COLLATE NOCASE""", (prefix, prefix + "\uffff")).fetchone()[0]
    return total


def _pot_files(inv, roots, after=None, limit=BATCH_SIZE):
    """Fetch at most limit rows per pot from the existing metadata map."""
    found = {}
    for root in roots:
        prefix = root.rstrip("\\/") + os.sep
        sql = """SELECT path,parent,name,extension,size,modified FROM items
          WHERE kind='file' AND path>=? COLLATE NOCASE AND path<? COLLATE NOCASE"""
        params = [prefix, prefix + "\uffff"]
        if after:
            sql += " AND path>? COLLATE NOCASE"
            params.append(after)
        sql += " ORDER BY path COLLATE NOCASE,path LIMIT ?"
        params.append(limit)
        for row in inv.execute(sql, params).fetchall():
            path = os.path.abspath(os.path.normpath(row["path"] if isinstance(row, sqlite3.Row) else row[0]))
            if _inside(path, root) and path.casefold() != root.casefold():
                found[path.casefold()] = (path, row)
    return sorted(found.values(), key=lambda item: (_sqlite_nocase_key(item[0]), item[0]))[:limit]


def _project_candidates(db):
    try:
        with closing(sqlite3.connect(f"file:{inventario.DB_FILE.as_posix()}?mode=ro", uri=True, timeout=3)) as inv:
            rows = inv.execute("SELECT path,name,kind,evidence FROM projects ORDER BY path").fetchall()
        return rows
    except sqlite3.Error:
        return []


def _match(name, projects):
    # La extensión/formato no identifica un proyecto (p. ej., CSV no es
    # evidencia para asociar un archivo con el plugin rainbow-csv).
    tokens = set(re.findall(r"[a-z0-9]{3,}", Path(name).stem.casefold())) - GENERIC_TOKENS
    scored = []
    for path, project, kind, evidence in projects:
        pt = set(re.findall(r"[a-z0-9]{3,}", str(project).casefold()))
        pt -= GENERIC_TOKENS
        overlap = tokens & pt
        # Un token común no basta para asignar un archivo a un árbol.
        # Un nombre de proyecto de una sola palabra aún puede coincidir si
        # esa palabra sobrevivió al filtro genérico.
        if overlap and (len(overlap) >= 2 or len(pt) == 1):
            scored.append((len(overlap) / max(1, len(pt)), project, path, sorted(overlap), kind))
    scored.sort(reverse=True)
    if not scored or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        return None, None, {"type": "metadata_name_match", "candidates": [
            {"project": x[1], "path": x[2], "matched_tokens": x[3], "score": round(x[0], 3)}
            for x in scored[:5]], "result": "REVIEW"}
    score, project, path, overlap, kind = scored[0]
    return project, path, {"type": "metadata_name_match", "project_kind": kind,
        "matched_tokens": overlap, "score": round(score, 3), "result": "candidate_only"}


def start():
    roots = _roots()
    if not roots:
        return {"status": "error", "error": "No hay dos macetas configuradas en runtime.json."}
    if not inventario.DB_FILE.exists():
        return {"status": "error", "error": "No existe un mapa de metadatos local."}
    with closing(sqlite3.connect(f"file:{inventario.DB_FILE.as_posix()}?mode=ro", uri=True, timeout=5)) as inv:
        total = _pot_file_count(inv, roots)
    db = _connect()
    cur = db.execute("INSERT INTO jobs(created_at,updated_at,status,roots,total) VALUES(?,?,?,?,?)",
                     (_now(), _now(), "running", json.dumps(roots, ensure_ascii=False), total))
    job_id = cur.lastrowid
    db.commit(); db.close()
    return process(job_id)


def process(job_id=None):
    db = _connect()
    job = db.execute("SELECT * FROM jobs WHERE id=?" if job_id else "SELECT * FROM jobs ORDER BY id DESC LIMIT 1",
                     (job_id,) if job_id else ()).fetchone()
    if not job:
        db.close(); return status()
    roots = json.loads(job["roots"])
    with closing(sqlite3.connect(f"file:{inventario.DB_FILE.as_posix()}?mode=ro", uri=True, timeout=5)) as inv:
        inv.row_factory = sqlite3.Row
        rows = _pot_files(inv, roots, after=job["cursor"], limit=BATCH_SIZE)
    rows = [{"path": path, **dict(row)} for path, row in rows]
    batch = rows[:BATCH_SIZE]
    projects = _project_candidates(db)
    for row in batch:
        name = row["name"]
        project, project_path, evidence = _match(name, projects)
        evidence.update({"source": "inventario.sqlite3", "observed": {
            "path": row["path"], "name": name, "extension": row["extension"],
            "size": row["size"], "modified": row["modified"]},
            "note": "No se leyó contenido ni se calculó hash."})
        # La ubicación del proyecto es solo una ruta candidata y queda bloqueada.
        destination = str(Path(project_path) / name) if project_path else None
        db.execute("""INSERT OR IGNORE INTO proposals(job_id,source,parent,name,extension,size,modified,
          project,project_path,evidence,proposed_name,proposed_destination,state,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (job["id"], row["path"], row["parent"], name, row["extension"], row["size"],
           row["modified"], project, project_path, json.dumps(evidence, ensure_ascii=False),
           name, destination, "REVIEW_BLOCKED" if destination else "REVIEW", _now()))
    cursor = batch[-1]["path"] if batch else job["cursor"]
    processed = db.execute("SELECT count(*) FROM proposals WHERE job_id=?", (job["id"],)).fetchone()[0]
    total = job["total"]
    complete = processed >= total or not batch
    db.execute("UPDATE jobs SET updated_at=?,status=?,cursor=?,processed=? WHERE id=?",
               (_now(), "complete" if complete else "running", cursor, processed, job["id"]))
    db.commit(); db.close()
    return status(job["id"])


def status(job_id=None):
    if not DB_FILE.exists():
        return {"status": "not_started", "processed": 0, "total": 0, "proposals": []}
    db = _connect()
    job = db.execute("SELECT * FROM jobs WHERE id=?" if job_id else "SELECT * FROM jobs ORDER BY id DESC LIMIT 1",
                     (job_id,) if job_id else ()).fetchone()
    if not job:
        db.close(); return {"status": "not_started", "processed": 0, "total": 0, "proposals": []}
    counts = {r["state"]: r["n"] for r in db.execute("SELECT state,count(*) n FROM proposals WHERE job_id=? GROUP BY state", (job["id"],))}
    proposals = [dict(r) for r in db.execute("SELECT id,source,name,extension,size,project,project_path,evidence,proposed_name,proposed_destination,state FROM proposals WHERE job_id=? ORDER BY id DESC LIMIT 30", (job["id"],))]
    db.close()
    for p in proposals:
        p["evidence"] = json.loads(p["evidence"])
    return {"job_id": job["id"], "status": job["status"], "processed": job["processed"],
            "total": job["total"], "counts": counts, "proposals": proposals,
            "updated_at": job["updated_at"], "mode": "proposal_only"}
