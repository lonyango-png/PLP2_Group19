class AlertsAndReportsService:
    pass

from datetime import date, datetime, timedelta


class AlertsAndReportsService:
    """Handles expiry alerts, low-stock alerts, and sales totals."""
    def _init_(self, db):
        self.db = db

    def get_expiring_soon(self, days_window: int = 90):
        conn = self.db.connect()
        cur = conn.cursor(dictionary=True)
        try:
            today = date.today()
            cutoff = today + timedelta(days=days_window)
            cur.execute(
                """
                SELECT
                    b.batch_number,
                    b.quantity,
                    b.expiry_date,
                    m.name AS medicine_name
                FROM batches b
                JOIN medicines m ON m.id = b.medicine_id
                WHERE b.is_active = 1
                  AND m.is_active = 1
                  AND b.quantity > 0
                  AND b.expiry_date >= %s
                  AND b.expiry_date <= %s
                ORDER BY b.expiry_date ASC, b.id ASC
                 """,
                (today.isoformat(), cutoff.isoformat()),
            )
            rows = cur.fetchall()
            for row in rows:
                exp = row["expiry_date"]
                if isinstance(exp, datetime):
                    exp = exp.date()
                row["days_left"] = (exp - today).days
            return rows
        finally:
            cur.close()
            conn.close()
    def get_expired_batches(self):
        conn = self.db.connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT
                    b.batch_number,
                    b.quantity,
                    b.expiry_date,
                    m.name AS medicine_name
                FROM batches b
                JOIN medicines m ON m.id = b.medicine_id
                WHERE b.is_active = 1
                  AND m.is_active = 1
                  AND b.quantity > 0
                  AND b.expiry_date < %s
                ORDER BY b.expiry_date ASC
                """,
                (self.db.today_str(),),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
    def today_sales_summary(self):
        conn = self.db.connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS sales_count,
                    COALESCE(SUM(total_amount), 0) AS revenue
                FROM sales
                WHERE DATE(sold_at) = CURDATE()
                  AND status = 'completed'
                """
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()