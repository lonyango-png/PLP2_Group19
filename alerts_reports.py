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