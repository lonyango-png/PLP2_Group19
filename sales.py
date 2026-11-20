class SalesService:
    """Handles FEFO sales recording, viewing sales, and voiding sales."""

    def __init__(self, db):
        self.db = db

    def record_fefo_sale(self, medicine_id: int, quantity_needed: int, user_id=None):
        if quantity_needed <= 0:
            raise ValueError("Quantity sold must be greater than 0.")
