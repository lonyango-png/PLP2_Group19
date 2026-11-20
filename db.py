from datetime import date
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

    def _server_connect(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
        )

    def connect(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
        )

    def init_db(self):
        server_conn = self._server_connect()
        cur = server_conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server_conn.commit()
        cur.close()
        server_conn.close()

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(30) NOT NULL UNIQUE,
                full_name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('pharmacist', 'attendant') NOT NULL DEFAULT 'attendant',
                is_active TINYINT(1) NOT NULL DEFAULT 1
            ) ENGINE=InnoDB
        """)
    
