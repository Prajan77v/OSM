import hashlib
import hmac
import secrets
import time
from datetime import datetime
from typing import Any, Dict, Optional
from db_engine import db_instance

def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        if '$' not in password_hash:
            return False
        salt, stored = password_hash.split('$', 1)
        check = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        return hmac.compare_digest(stored, check)
    except Exception:
        return False

class AuthEngine:
    def __init__(self):
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._ensure_default_admin()

    def _ensure_default_admin(self):
        try:
            conn = db_instance._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
            row = cur.fetchone()
            if not row or not verify_password('admin123', dict(row)['password_hash']):
                pass_hash = hash_password('admin123')
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("DELETE FROM users WHERE username = 'admin'")
                cur.execute('INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)', ('admin', pass_hash, 'Admin', now))
                conn.commit()
            conn.close()
        except Exception as ex:
            print("Ensure admin error:", ex)

    def login(self, username: str, password: str, ip_address: str = '127.0.0.1') -> Optional[Dict[str, Any]]:
        conn = db_instance._get_connection()
        try:
            cur = conn.cursor()
            cur.execute('SELECT username, password_hash, role FROM users WHERE username = ?', (username.strip(),))
            row = cur.fetchone()
            if not row:
                db_instance.log_audit('system', 'login_failed', ip_address, f'Invalid username: {username}')
                return None
            user_dict = dict(row)
            if not verify_password(password, user_dict['password_hash']):
                db_instance.log_audit(username, 'login_failed', ip_address, 'Incorrect password')
                return None
            token = secrets.token_hex(24)
            expiry = time.time() + 86400
            user_info = {'username': user_dict['username'], 'role': user_dict['role'], 'token': token, 'expires_at': expiry}
            self._tokens[token] = user_info
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute('UPDATE users SET last_login = ? WHERE username = ?', (now, username))
            conn.commit()
            db_instance.log_audit(username, 'login_success', ip_address, f'Role: {user_dict["role"]}')
            return user_info
        finally:
            conn.close()

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        info = self._tokens.get(token)
        if not info:
            return None
        if time.time() > info['expires_at']:
            self._tokens.pop(token, None)
            return None
        return info

    def check_permission(self, token: str, required_role: str = 'Viewer') -> bool:
        info = self.verify_token(token)
        if not info:
            return False
        user_role = info.get('role', 'Viewer')
        role_levels = {'Viewer': 1, 'Operator': 2, 'Admin': 3}
        return role_levels.get(user_role, 0) >= role_levels.get(required_role, 1)

auth_instance = AuthEngine()