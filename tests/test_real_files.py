"""Pruebas reales de E/S en directorios aislados; no usa el perfil Windows."""
import importlib.util
import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'jardinero.py'
spec = importlib.util.spec_from_file_location('jardinero', MODULE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class JardinPhysicalTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.base = Path(self.folder.name)
        self.pots = [self.base / 'Downloads' / '00_MACETA', self.base / 'Desktop' / '00_MACETA']
        self.root = self.base / 'garden'
        self.state = self.base / 'state'
        self.rt = {'garden_root': str(self.root), 'state_dir': str(self.state), 'pots': [str(p) for p in self.pots]}
        self.cfg = {'classify_model': 'test-model', 'embed_model': 'test-embed', 'min_confidence': 0.85,
                    'max_items_per_run': 30, 'max_backup_bytes': 500000, 'max_item_bytes': 500000}
        g.init(self.rt)
        self.verdict = {'domain': 'Ingenieria', 'project': 'Robotica',
                        'description': 'calibracion_de_motor', 'confidence': 0.95, 'reason': 'contenido tecnico'}

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, content='Posicion y calibracion del motor paso a paso'):
        path = self.pots[0] / name
        path.write_text(content, encoding='utf-8')
        os.utime(path, (time.time() - 120, time.time() - 120))
        return path

    def run_once(self):
        with patch.object(g, 'installed_models', return_value={'test-model'}), \
             patch.object(g, 'llm_classify', return_value=self.verdict):
            return g.run(self.rt, self.cfg)

    def test_real_move_digest_search_and_restore(self):
        src = self.write('motor.txt')
        digest = g.sha256(src)
        self.assertEqual(self.run_once(), 0)
        self.assertFalse(src.exists())
        db = g.db_connect(self.state / 'index.sqlite3')
        op, dest, got_sha = db.execute('SELECT id,dest,digest FROM moves WHERE status="COMPLETE"').fetchone()
        self.assertTrue(Path(dest).exists())
        self.assertEqual(got_sha, digest)
        self.assertEqual(g.sha256(Path(dest)), digest)
        result = db.execute("SELECT body FROM fts_docs WHERE fts_docs MATCH 'calibracion'").fetchall()
        self.assertTrue(result)
        db.close()
        g.undo(self.rt, op)
        self.assertTrue(src.exists())
        self.assertEqual(g.sha256(src), digest)
        self.assertTrue(Path(dest).exists())  # Ningún borrado en undo

    def test_no_move_without_model(self):
        src = self.write('sensor.txt')
        with patch.object(g, 'installed_models', return_value=set()):
            self.assertEqual(g.run(self.rt, self.cfg), 2)
        self.assertTrue(src.exists())

    def test_uncertain_remains_in_pot(self):
        src = self.write('unknown.txt')
        bad = dict(self.verdict, confidence=.4)
        with patch.object(g, 'installed_models', return_value={'test-model'}), \
             patch.object(g, 'llm_classify', return_value=bad):
            self.assertEqual(g.run(self.rt, self.cfg), 0)
        self.assertTrue(src.exists())

    def test_deny_secret(self):
        src = self.write('.env.secret', 'PASSWORD=123')
        self.assertEqual(self.run_once(), 0)
        self.assertTrue(src.exists())

    def test_folder_moved_as_whole_unit(self):
        parent = self.pots[1] / 'RobotProyecto'
        parent.mkdir()
        (parent / 'main.cpp').write_text('Control PID', encoding='utf-8')
        os.utime(parent / 'main.cpp', (time.time()-120, time.time()-120))
        os.utime(parent, (time.time()-120, time.time()-120))
        self.assertEqual(self.run_once(), 0)
        self.assertFalse(parent.exists())
        self.assertEqual(len(list(self.root.rglob('main.cpp'))), 1)

    def test_reconcile_after_moved_but_not_indexed(self):
        src = self.write('protocol.txt')
        digest = g.sha256(src)
        dst = self.root / 'Ingenieria' / 'Robotica' / '20261101' / 'protocol' / 'ficha_tecnica.txt'
        dst.parent.mkdir(parents=True)
        src.rename(dst)
        db = g.db_connect(self.state / 'index.sqlite3')
        db.execute('INSERT INTO moves VALUES (?,?,?,?,?,?,?,?,?)', ('op', str(src), str(dst), digest, '', 'MOVED',
                                                                  g.timestamp(), g.timestamp(), None))
        db.commit()
        db.close()
        with patch.object(g, 'installed_models', return_value={'test-model'}), \
             patch.object(g, 'llm_classify', return_value=self.verdict):
            self.assertEqual(g.run(self.rt, self.cfg), 0)
        db = g.db_connect(self.state / 'index.sqlite3')
        self.assertEqual(db.execute('SELECT status FROM moves WHERE id="op"').fetchone()[0], 'COMPLETE')
        self.assertEqual(db.execute('SELECT COUNT(*) FROM docs').fetchone()[0], 1)
        db.close()


if __name__ == '__main__':
    unittest.main()
