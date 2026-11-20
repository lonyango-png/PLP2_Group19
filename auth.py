import os
import hashlib

class AuthService:
    def __init__(self, db):
        self.db = db
        self._ensure_default_admin()

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16).hex()
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return f"{salt}${digest}"

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        if "$" not in stored_hash:
            return False
        salt, expected = stored_hash.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return actual == expected

    def _ensure_default_admin(self):
        conn = self.db.connect()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO users (username, full_name, password_hash, role, is_active)
                    VALUES (%s, %s, %s, 'pharmacist', 1)
                    """,
                    ("admin", "Default Pharmacist", self.hash_password("admin123")),
                )
                conn.commit()
        finally:
            cur.close()
            conn.close()


