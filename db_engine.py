import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class DatabaseEngine:
    def __init__(self, db_type: str = 'sqlite', db_path: Optional[Path] = None, pg_dsn: str = ''):
        self.db_type = db_type.lower()
        self.db_path = db_path or (Path(__file__).parent / 'oms_sentinel_v10.db')
        self.pg_dsn = pg_dsn
        self._lock = threading.RLock()
        self._init_tables()

    def _get_connection(self):
        if self.db_type == 'postgresql' and self.pg_dsn:
            try:
                import psycopg2
                return psycopg2.connect(self.pg_dsn)
            except Exception:
                self.db_type = 'sqlite'
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'Operator', created_at TEXT NOT NULL, last_login TEXT)''')
                cur.execute('''CREATE TABLE IF NOT EXISTS security_events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, event_type TEXT NOT NULL, camera TEXT, person TEXT, detail TEXT, threat_level TEXT DEFAULT 'GREEN')''')
                cur.execute('''CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, username TEXT NOT NULL, action TEXT NOT NULL, ip_address TEXT, detail TEXT)''')
                cur.execute('''CREATE TABLE IF NOT EXISTS analytics_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, camera_id INT NOT NULL, person_count INT DEFAULT 0, object_count INT DEFAULT 0, heatmap_data TEXT)''')
                conn.commit()
            finally:
                conn.close()

    def log_event(self, event_type: str, camera: str = '', person: str = '', detail: str = '', threat_level: str = 'GREEN'):
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute('INSERT INTO security_events (ts, event_type, camera, person, detail, threat_level) VALUES (?, ?, ?, ?, ?, ?)', (ts, event_type, camera, person, detail, threat_level))
                conn.commit()
            finally:
                conn.close()

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute('SELECT ts, event_type as event, camera, person, detail, threat_level FROM security_events ORDER BY id DESC LIMIT ?', (limit,))
                return [dict(r) for r in cur.fetchall()]
            finally:
                conn.close()

    def log_audit(self, username: str, action: str, ip_address: str = '127.0.0.1', detail: str = ''):
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute('INSERT INTO audit_logs (ts, username, action, ip_address, detail) VALUES (?, ?, ?, ?, ?)', (ts, username, action, ip_address, detail))
                conn.commit()
            finally:
                conn.close()

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute('SELECT ts, username, action, ip_address, detail FROM audit_logs ORDER BY id DESC LIMIT ?', (limit,))
                return [dict(r) for r in cur.fetchall()]
            finally:
                conn.close()

db_instance = DatabaseEngine()