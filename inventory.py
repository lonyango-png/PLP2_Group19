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