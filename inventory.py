from datetime import date, datetime
class InventoryService:
#Handles medicines, batches, search, and computed stock status.

    def _init_(self, db):
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
