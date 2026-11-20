
class SalesService:
    """Handles FEFO sales recording, viewing sales, and voiding sales."""

    def __init__(self, db):
        self.db = db
