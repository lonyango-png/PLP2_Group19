from datetime import date
import os
import mysql.connector

class PharmaDatabase:
    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.host = host or os.getenv("PHARMA_DB_HOST")
        self.user = user or os.getenv("PHARMA_DB_USER")
        self.password = password if password is not None else os.getenv("PHARMA_DB_PASSWORD")
        self.database = database or os.getenv("PHARMA_DB_NAME")
        self.port = int(port or os.getenv("PHARMA_DB_PORT", 3306))
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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                unit_price DECIMAL(10, 2) NOT NULL,
                reorder_level INT NOT NULL DEFAULT 20,
                is_active TINYINT(1) NOT NULL DEFAULT 1
            ) ENGINE=InnoDB
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                medicine_id INT NOT NULL,
                batch_number VARCHAR(50) NOT NULL,
                quantity INT NOT NULL,
                expiry_date DATE NOT NULL,
                received_date DATE NOT NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                CONSTRAINT fk_batches_med FOREIGN KEY (medicine_id) REFERENCES medicines(id),
                UNIQUE KEY uq_med_batch (medicine_id, batch_number),
                INDEX idx_med_expiry (medicine_id, expiry_date)
            ) ENGINE=InnoDB
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                total_amount DECIMAL(12, 2) NOT NULL,
                status ENUM('completed', 'voided') NOT NULL DEFAULT 'completed',
                void_reason VARCHAR(255) NULL,
                sold_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_sales_user FOREIGN KEY (user_id) REFERENCES users(id),
                INDEX idx_sold_at (sold_at)
            ) ENGINE=InnoDB
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sale_id INT NOT NULL,
                batch_id INT NOT NULL,
                medicine_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10, 2) NOT NULL,
                CONSTRAINT fk_items_sale FOREIGN KEY (sale_id) REFERENCES sales(id),
                CONSTRAINT fk_items_batch FOREIGN KEY (batch_id) REFERENCES batches(id),
                CONSTRAINT fk_items_med FOREIGN KEY (medicine_id) REFERENCES medicines(id)
            ) ENGINE=InnoDB
        """)

        conn.commit()
        cur.close()
        conn.close()
           
    @staticmethod
    def today_str():
        return date.today().isoformat()
    
    
