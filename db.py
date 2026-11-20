import os
import mysql.connector

class PharmaDatabase:
    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.host = host or os.getenv("PHARMA_DB_HOST", "localhost")
        self.user = user or os.getenv("PHARMA_DB_USER", "root")
        self.password = password if password is not None else os.getenv("PHARMA_DB_PASSWORD", "")
        self.database = database or os.getenv("PHARMA_DB_NAME", "pharma_db")
        self.port = int(port or os.getenv("PHARMA_DB_PORT", "3306))
        self.init_db()
