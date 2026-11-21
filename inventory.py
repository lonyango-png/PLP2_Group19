from datetime import date, datetime
class InventoryService:
    # Handles medicines, batches, search, and computed stock status.

    def __init__(self, db):
        self.db = db

    @staticmethod
    def compute_status(sellable_qty: int, reorder_level: int) -> str:
        if sellable_qty <= 0:
            return "Out of Stock"
        if sellable_qty <= reorder_level:
            return "Low Stock"
        return "OK"
    
    def add_medicine_and_batch(
        self,
        name: str,
        batch_number: str,
        quantity: int,
        unit_price: float,
        expiry_date_str: str,
        reorder_level: int = 20,
    ):
        if quantity <= 0:
            raise ValueError("Quantity must be at least 1.")
        if unit_price <= 0:
            raise ValueError("Unit price must be greater than 0.")
        if reorder_level < 0:
            raise ValueError("Reorder level cannot be negative.")

        expiry_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        if expiry_dt <= date.today():
            raise ValueError("New batch expiry date must be in the future.")

        conn = self.db.connect()
        cur = conn.cursor()
        try:
            conn.start_transaction()
            cur.execute(
                """
                INSERT INTO medicines (name, unit_price, reorder_level, is_active)
                VALUES (%s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    unit_price = VALUES(unit_price),
                    reorder_level = VALUES(reorder_level),
                    is_active = 1
                """,
                (name, float(unit_price), int(reorder_level)),
            )

            cur.execute("SELECT id FROM medicines WHERE name = %s", (name,))
            med_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO batches
                    (medicine_id, batch_number, quantity, expiry_date, received_date, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
                """,
                (med_id, batch_number, int(quantity), expiry_dt.isoformat(), self.db.today_str()),
            )
            batch_id = cur.lastrowid
            conn.commit()
            return med_id, batch_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def search_medicines(self, keyword: str = ""):
        conn = self.db.connect()
        cur = conn.cursor(dictionary=True)
        try:
            today = self.db.today_str()
            cur.execute(
                """
                SELECT
                    m.id,
                    m.name,
                    m.unit_price,
                    m.reorder_level,
                    COALESCE(SUM(
                        CASE
                            WHEN b.is_active = 1 AND b.expiry_date >= %s AND b.quantity > 0
                            THEN b.quantity ELSE 0
                        END
                    ), 0) AS sellable_qty,
                    MIN(
                        CASE
                            WHEN b.is_active = 1 AND b.expiry_date >= %s AND b.quantity > 0
                            THEN b.expiry_date ELSE NULL
                        END
                    ) AS nearest_expiry
                FROM medicines m
                LEFT JOIN batches b ON b.medicine_id = m.id
                WHERE m.is_active = 1
                  AND m.name LIKE %s
                GROUP BY m.id, m.name, m.unit_price, m.reorder_level
                ORDER BY m.name ASC
                """,
                (today, today, f"%{keyword}%"),
            )
            rows = cur.fetchall()
            for r in rows:
                r["status"] = self.compute_status(r["sellable_qty"], r["reorder_level"])
            return rows
        finally:
            cur.close()
            conn.close()
