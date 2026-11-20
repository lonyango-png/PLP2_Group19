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
