# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>

"""Descubrimiento determinista de repositorios y módulos desde el mapa de metadatos."""
from __future__ import annotations

import json
import os
import configparser
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import inventario

DB_FILE = inventario.DB_FILE
_lock = threading.Lock()
_thread: threading.Thread | None = None

MANIFESTS = {
    "package.json", "pyproject.toml", "cargo.toml", "go.mod", "pom.xml",
    "build.gradle", "build.gradle.kts", "composer.json", "cmakelists.txt",
    "deno.json", "deno.jsonc", "pubspec.yaml", "mix.exs", "makefile",
    "flake.nix", "justfile",
}
MANIFEST_EXTENSIONS = {".sln", ".csproj", ".fsproj", ".vbproj", ".xcworkspace", ".xcodeproj"}
IGNORED_COMPONENTS = {
    "$recycle.bin", "windows", "program files", "program files (x86)",
    "programdata", "appdata", "node_modules", "vendor", "site-packages",
    ".venv", "venv", "__pycache__", "dist", "build", ".npm", ".cargo", ".obsidian",
    ".codex", ".gemini", ".platformio", ".cache", "cache", "worktrees", "backups",
    ".pio", ".vscode", ".arduinoide", "verification", "recovery", "node_modules", "vendor", "site-packages",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _db(readonly=False):
    if readonly:
        return sqlite3.connect(f"file:{DB_FILE.as_posix()}?mode=ro", uri=True, timeout=5)
    db = sqlite3.connect(DB_FILE, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA busy_timeout=60000")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS project_discovery(
        id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        finished_at TEXT, status TEXT NOT NULL, marker_count INTEGER NOT NULL DEFAULT 0,
        project_count INTEGER NOT NULL DEFAULT 0, module_count INTEGER NOT NULL DEFAULT 0,
        error TEXT, items_scanned INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE IF NOT EXISTS projects(
        path TEXT PRIMARY KEY COLLATE NOCASE, name TEXT NOT NULL, kind TEXT NOT NULL,
        volume TEXT NOT NULL, plot_path TEXT NOT NULL, evidence TEXT NOT NULL,
        file_count INTEGER NOT NULL DEFAULT 0, dir_count INTEGER NOT NULL DEFAULT 0,
        bytes INTEGER NOT NULL DEFAULT 0, branch_count INTEGER NOT NULL DEFAULT 0,
        module_count INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE IF NOT EXISTS project_modules(
        path TEXT PRIMARY KEY COLLATE NOCASE, project_path TEXT NOT NULL COLLATE NOCASE,
        name TEXT NOT NULL, evidence TEXT NOT NULL);
      CREATE INDEX IF NOT EXISTS project_modules_root ON project_modules(project_path);
      CREATE TABLE IF NOT EXISTS project_candidates(
        path TEXT PRIMARY KEY COLLATE NOCASE, name TEXT NOT NULL, kind TEXT NOT NULL,
        markers TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'REVIEW');
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(project_discovery)")}
    if "items_scanned" not in columns:
        db.execute("ALTER TABLE project_discovery ADD COLUMN items_scanned INTEGER NOT NULL DEFAULT 0")
    if "candidate_count" not in columns:
        db.execute("ALTER TABLE project_discovery ADD COLUMN candidate_count INTEGER NOT NULL DEFAULT 0")
    return db


def _is_ignored(path: str) -> bool:
    return any(part.casefold() in IGNORED_COMPONENTS for part in Path(path).parts)


def _repo_identity(root: str) -> str:
    """Read Git metadata only; never invoke Git or execute repository hooks."""
    marker = Path(root) / ".git"
    try:
        gitdir = marker.resolve() if marker.is_dir() else None
        if marker.is_file():
            match = re.search(r"(?im)^gitdir:\s*(.+?)\s*$", marker.read_text(encoding="utf-8", errors="replace"))
            if match:
                gitdir = (Path(root) / match.group(1)).resolve()
        if not gitdir:
            return "path:" + os.path.normcase(os.path.abspath(root))
        common = gitdir
        common_file = gitdir / "commondir"
        if common_file.is_file():
            common = (gitdir / common_file.read_text(encoding="utf-8", errors="replace").strip()).resolve()
        cfg = configparser.ConfigParser(interpolation=None, strict=False)
        cfg.read(common / "config", encoding="utf-8")
        remote = cfg.get('remote "origin"', "url", fallback="").strip().casefold()
        remote = re.sub(r"^https?://[^/@]+(?::[^/@]*)?@", "https://", remote)
        remote = re.sub(r"\.git/?$", "", remote).rstrip("/")
        if remote:
            return "origin:" + remote
        return "common:" + os.path.normcase(str(common))
    except (OSError, ValueError, configparser.Error):
        return "path:" + os.path.normcase(os.path.abspath(root))


def _canonical_preference(root: str) -> tuple[int, int, str]:
    low = root.casefold()
    archival = any(token in low for token in ("_archive", "\\backup", "\\restored", "\\verification", "\\recovery", "\\worktrees"))
    canonical = "canonical" in low or "\\work\\" in low
    return (1 if archival else 0, 0 if canonical else 1, low)


def _ancestors(path: str):
    current = path.rstrip("\\/")
    while current:
        yield current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent.rstrip("\\/")


def _inside(path: str, root: str) -> bool:
    p, r = path.casefold().rstrip("\\/"), root.casefold().rstrip("\\/")
    return p == r or p.startswith(r + "\\") or p.startswith(r + "/")


def _subtree_stats(db: sqlite3.Connection, root: str):
    low = root.rstrip("\\/")
    high = low + "\\\uffff"
    return db.execute("""SELECT
        sum(CASE WHEN kind='file' THEN 1 ELSE 0 END),
        sum(CASE WHEN kind='directory' THEN 1 ELSE 0 END),
        sum(CASE WHEN kind='file' THEN coalesce(size,0) ELSE 0 END)
        FROM items WHERE path>=? COLLATE NOCASE AND path<? COLLATE NOCASE""", (low, high)).fetchone()


def _aggregate_project_stats(db: sqlite3.Connection, roots: list[str], run_id: int, allowed_roots: list[str]):
    """Cuenta todos los subárboles en una sola pasada, incluyendo raíces anidadas."""
    by_path = {root.casefold().rstrip("\\/"): i for i, root in enumerate(roots)}
    totals = [[0, 0, 0] for _ in roots]
    scanned = 0
    reader = sqlite3.connect(f"file:{DB_FILE.as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        marks = ",".join("?" for _ in allowed_roots)
        cursor = reader.execute(f"SELECT path,kind,size FROM items WHERE root IN ({marks}) ORDER BY path COLLATE NOCASE", allowed_roots)
        while True:
            batch = cursor.fetchmany(20_000)
            if not batch:
                break
            for path, kind, size in batch:
                current = path.rstrip("\\/")
                while current:
                    slot = by_path.get(current.casefold())
                    if slot is not None:
                        if kind == "file":
                            totals[slot][0] += 1
                            totals[slot][2] += int(size or 0)
                        elif kind == "directory":
                            totals[slot][1] += 1
                    parent = os.path.dirname(current)
                    if parent == current:
                        break
                    current = parent.rstrip("\\/")
                scanned += 1
            db.execute("UPDATE project_discovery SET status='resumiendo_mapa',project_count=?,items_scanned=?,updated_at=? WHERE id=?",
                       (len(roots), scanned, _now(), run_id))
            db.commit()
    finally:
        reader.close()
    return totals


def start() -> dict:
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return status()
        state = status()
        db = _db()
        row = db.execute("SELECT id FROM project_discovery ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            run_id = row[0]
            db.execute("UPDATE project_discovery SET status='indexando',updated_at=?,finished_at=NULL,error=NULL WHERE id=?",
                       (_now(), run_id))
        else:
            now = _now()
            run_id = db.execute("INSERT INTO project_discovery(started_at,updated_at,status) VALUES(?,?,?)",
                                (now, now, "indexando")).lastrowid
        db.commit()
        db.close()
        _thread = threading.Thread(target=_worker, args=(run_id,), name="JardineroProyectos", daemon=True)
        _thread.start()
    return status()


def status() -> dict:
    if not DB_FILE.exists():
        return {"status": "not_started", "projects": 0, "modules": 0, "markers": 0}
    try:
        db = _db(readonly=True)
        table = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='project_discovery'").fetchone()
        if not table:
            db.close()
            return {"status": "not_started", "projects": 0, "modules": 0, "markers": 0}
        row = db.execute("SELECT id,started_at,updated_at,finished_at,status,marker_count,project_count,module_count,error,items_scanned,candidate_count FROM project_discovery ORDER BY id DESC LIMIT 1").fetchone()
        shrubs = db.execute("SELECT count(*) FROM project_candidates WHERE status='REVIEW'").fetchone()[0]
        db.close()
        if not row:
            return {"status": "not_started", "projects": 0, "modules": 0, "markers": 0}
        alive = bool(_thread and _thread.is_alive())
        state = "interrupted" if row[4] in ("running", "indexando") and not alive else row[4]
        return {"run_id": row[0], "started_at": row[1], "updated_at": row[2], "finished_at": row[3],
                "status": state, "markers": row[5], "projects": row[6], "modules": row[7],
                "error": row[8], "items_scanned": row[9], "shrubs": max(shrubs, row[10] or 0), "worker_alive": alive}
    except sqlite3.Error as exc:
        return {"status": "error", "error": str(exc), "projects": 0, "modules": 0, "markers": 0}


def overview(limit=400) -> dict:
    result = status()
    if result.get("status") not in ("complete", "complete_with_errors"):
        result["items"] = []
        result["total"] = result.get("projects", 0)
        return result
    db = _db(readonly=True)
    rows = db.execute("""SELECT path,name,kind,volume,plot_path,evidence,file_count,dir_count,bytes,
        branch_count,module_count FROM projects ORDER BY bytes DESC,name COLLATE NOCASE LIMIT ?""", (limit,)).fetchall()
    result["items"] = [dict(zip(("path","name","kind","volume","plot","evidence","files","directories","bytes","branches","modules"), row)) for row in rows]
    result["total"] = db.execute("SELECT count(*) FROM projects").fetchone()[0]
    db.close()
    return result


def detail(path: str) -> dict:
    db = _db(readonly=True)
    row = db.execute("SELECT path,name,kind,volume,plot_path,evidence,file_count,dir_count,bytes,branch_count,module_count FROM projects WHERE path=? COLLATE NOCASE", (path,)).fetchone()
    if not row:
        db.close()
        return {"error": "No se encontró ese árbol en el mapa de proyectos."}
    project = dict(zip(("path","name","kind","volume","plot","evidence","files","directories","bytes","branches","modules"), row))
    project["module_items"] = [dict(path=p, name=n, evidence=e) for p,n,e in db.execute(
        "SELECT path,name,evidence FROM project_modules WHERE project_path=? COLLATE NOCASE ORDER BY path LIMIT 100", (path,))]
    project["branch_items"] = [dict(path=p,name=n) for p,n in db.execute(
        "SELECT path,name FROM items WHERE parent=? COLLATE NOCASE AND kind='directory' ORDER BY name COLLATE NOCASE LIMIT 80", (path,))]
    db.close()
    return project


def _worker(run_id: int) -> None:
    db = None
    try:
        # Un índice por nombre evita volver a recorrer 3.4 millones de filas para cada marcador.
        db = _db()
        db.execute("UPDATE project_discovery SET status='indexando',updated_at=? WHERE id=?", (_now(), run_id)); db.commit()
        db.execute("CREATE INDEX IF NOT EXISTS items_name ON items(name COLLATE NOCASE)")
        db.execute("CREATE INDEX IF NOT EXISTS items_extension ON items(extension COLLATE NOCASE)")
        db.execute("CREATE INDEX IF NOT EXISTS items_tree_metrics ON items(path COLLATE NOCASE,kind,size)")
        db.commit()
        db.execute("UPDATE project_discovery SET status='analizando',updated_at=? WHERE id=?", (_now(), run_id)); db.commit()
        manifest_names = tuple(sorted(MANIFESTS | {".git"}))
        name_marks = ",".join("?" for _ in manifest_names)
        run = db.execute("SELECT roots FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        allowed_roots = json.loads(run[0]) if run else []
        if not allowed_roots:
            raise RuntimeError("El mapa no tiene raíces físicas autorizadas registradas.")
        root_marks = ",".join("?" for _ in allowed_roots)
        manifest_rows = db.execute(f"SELECT path,parent,name FROM items WHERE root IN ({root_marks}) AND name COLLATE NOCASE IN ({name_marks})",
                                   (*allowed_roots, *manifest_names)).fetchall()
        manifest_extensions = tuple(sorted(MANIFEST_EXTENSIONS))
        ext_marks = ",".join("?" for _ in manifest_extensions)
        extension_rows = db.execute(f"SELECT path,parent,name FROM items WHERE root IN ({root_marks}) AND extension COLLATE NOCASE IN ({ext_marks})",
                                    (*allowed_roots, *manifest_extensions)).fetchall()
        rows = manifest_rows + extension_rows
        db.execute("UPDATE project_discovery SET status='agrupando_marcadores',marker_count=?,updated_at=? WHERE id=?",
                   (len(rows), _now(), run_id)); db.commit()
        git_roots = {}
        markers_by_dir: dict[str, set[str]] = {}
        dir_paths = {}
        for path, parent, name in rows:
            if not parent or _is_ignored(path):
                continue
            key = parent.casefold().rstrip("\\/")
            dir_paths[key] = parent.rstrip("\\/")
            markers_by_dir.setdefault(key, set()).add(name)
            if name.casefold() == ".git":
                git_roots[key] = parent.rstrip("\\/")
        git_values = sorted(git_roots.values(), key=len)
        git_keys = {p.casefold(): p for p in git_values}
        module_map: dict[str, dict[str, set[str]]] = {k: {} for k in git_keys}
        standalone = []
        for key, markers in markers_by_dir.items():
            path = next((p for p in git_keys.values() if _inside(key, p)), None)
            if path:
                if key != path.casefold():
                    module_map[path.casefold()][dir_paths[key]] = markers
            else:
                # Makefile por sí solo es común en documentación y paquetes instalados;
                # conservarlo como evidencia dentro de un Git, pero no sembrar árboles con él.
                if all(marker.casefold() == "makefile" for marker in markers):
                    continue
                standalone.append((key, markers))
        standalone.sort(key=lambda item: (len(item[0]), item[0]))
        stand_roots: dict[str, tuple[str, set[str]]] = {}
        for key, markers in standalone:
            # La cadena de ancestros da coste O(profundidad), no O(n²) sobre
            # miles de carpetas con manifiestos de dependencias instaladas.
            parent_roots = (ancestor.casefold().rstrip("\\/") for ancestor in _ancestors(key))
            if any(ancestor != key and ancestor in stand_roots for ancestor in parent_roots):
                continue
            # La clave es siempre normalizada; el casing original se conserva
            # como valor para mostrar la ruta al usuario.
            stand_roots[key] = (dir_paths[key], markers)
        db.execute("UPDATE project_discovery SET status='consolidando_arboles',project_count=?,candidate_count=?,updated_at=? WHERE id=?",
                   (len(git_roots), len(stand_roots), _now(), run_id)); db.commit()
        projects = []
        modules = []
        shrubs = [(path, os.path.basename(path.rstrip("\\/")) or path,
                   json.dumps(sorted(markers, key=str.casefold), ensure_ascii=False), "REVIEW")
                  for path, markers in stand_roots.values() if not _is_ignored(path)]
        # Sólo una raíz Git independiente crea un árbol. Manifiestos fuera de
        # Git quedan como evidencia/módulos; no se cuentan como proyectos.
        raw_roots = sorted(git_roots.values(), key=lambda p: (len(p), p.casefold()))
        top_roots = [root for root in raw_roots
                     if not _is_ignored(root) and not any(_inside(root, other) for other in raw_roots if other != root)]
        grouped: dict[str, list[str]] = {}
        for root in top_roots:
            grouped.setdefault(_repo_identity(root), []).append(root)
        for group_index, (identity, candidates) in enumerate(grouped.items(), 1):
            candidates.sort(key=_canonical_preference)
            root = candidates[0]
            key = root.casefold()
            # Un marcador .git sin archivos no representa un árbol vivo.
            prefix = root.rstrip("\\/") + "\\"
            has_files = db.execute("SELECT 1 FROM items WHERE kind='file' AND path>=? COLLATE NOCASE AND path<? COLLATE NOCASE LIMIT 1",
                                   (prefix, prefix + "\uffff")).fetchone()
            if not has_files:
                continue
            root_modules = dict(module_map.get(key, {}))
            for duplicate in candidates[1:]:
                root_modules[duplicate] = {"same_repository_identity"}
            projects.append((root, "git", markers_by_dir.get(key, {".git"}), root_modules))
            if group_index % 5 == 0:
                db.execute("UPDATE project_discovery SET status='validando_arboles',project_count=?,updated_at=? WHERE id=?",
                           (group_index, _now(), run_id)); db.commit()
        projects.sort(key=lambda p: p[0].casefold())
        db.execute("UPDATE project_discovery SET status='resumiendo_mapa',project_count=?,updated_at=? WHERE id=?",
                   (len(projects), _now(), run_id)); db.commit()
        project_stats = _aggregate_project_stats(db, [p[0] for p in projects], run_id, allowed_roots)
        payload = []
        for index, (root, kind, markers, module_dirs) in enumerate(projects, 1):
            files, dirs, size = project_stats[index - 1]
            # Las rutas salen del mismo inventario y conservan exactamente su casing;
            # sin COLLATE NOCASE SQLite reutiliza el índice items_parent.
            direct_dirs = db.execute("SELECT count(*) FROM items WHERE parent=? AND kind='directory'", (root,)).fetchone()[0]
            volume = root[:2] if len(root) > 1 and root[1] == ":" else root.split("\\")[0]
            plot = os.path.dirname(root.rstrip("\\/")) or root
            payload.append((root, os.path.basename(root.rstrip("\\/")) or root, kind, volume, plot,
                            json.dumps(sorted(markers, key=str.casefold), ensure_ascii=False), files, dirs,
                            size, int(direct_dirs), len(module_dirs)))
            for module_key, evidence in module_dirs.items():
                module_name = os.path.basename(module_key.rstrip("\\/")) or module_key
                modules.append((module_key, root, module_name,
                                json.dumps(sorted(evidence, key=str.casefold), ensure_ascii=False)))
            if index % 25 == 0:
                db.execute("UPDATE project_discovery SET marker_count=?,project_count=?,module_count=?,updated_at=? WHERE id=?",
                           (len(rows), index, len(modules), _now(), run_id)); db.commit()
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM project_modules")
        db.execute("DELETE FROM projects")
        db.execute("DELETE FROM project_candidates")
        db.executemany("INSERT INTO projects(path,name,kind,volume,plot_path,evidence,file_count,dir_count,bytes,branch_count,module_count) VALUES(?,?,?,?,?,?,?,?,?,?,?)", payload)
        db.executemany("INSERT INTO project_modules(path,project_path,name,evidence) VALUES(?,?,?,?)", modules)
        db.executemany("INSERT INTO project_candidates(path,name,kind,markers,status) VALUES(?,?, 'shrub', ?,?)", shrubs)
        db.execute("UPDATE project_discovery SET status='complete',marker_count=?,project_count=?,module_count=?,candidate_count=?,updated_at=?,finished_at=?,error=NULL WHERE id=?",
                   (len(rows), len(payload), len(modules), len(shrubs), _now(), _now(), run_id))
        db.commit()
        try:
            import brain
            brain.sync_markdown()
        except Exception:
            pass
    except Exception as exc:
        if db:
            db.rollback()
            db.execute("UPDATE project_discovery SET status='interrupted',updated_at=?,error=? WHERE id=?",
                       (_now(), f"{type(exc).__name__}: {exc}"[:1000], run_id)); db.commit()
    finally:
        if db:
            db.close()
