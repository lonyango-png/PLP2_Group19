class SalesService:
    """Handles FEFO sales recording, viewing sales, and voiding sales."""

    def __init__(self, db):
        self.db = db

    def record_fefo_sale(self, medicine_id: int, quantity_needed: int, user_id=None):
        if quantity_needed <= 0:
            raise ValueError("Quantity sold must be greater than 0.")

        conn = self.db.connect()
        cur = conn.cursor()

        try:
            conn.start_transaction()
            cur.execute(
                "SELECT id, name, unit_price FROM medicines WHERE id = %s AND is_active = 1",
                (medicine_id,),
            )
            medicine = cur.fetchone()

            if medicine is None:
                raise ValueError("Medicine not found or inactive.")
            medicine_name = medicine[1]
            unit_price = medicine[2]

            cur.execute(
                """
                SELECT id, quantity, expiry_date
                FROM batches
                WHERE medicine_id = %s
                  AND quantity > 0
                  AND is_active = 1
                  AND expiry_date > %s
                ORDER BY expiry_date ASC, id ASC
                FOR UPDATE
                """,
                (medicine_id, self.db.today_str()),
            )
            batches = cur.fetchall()
            total_available = sum(batch[1] for batch in batches)
            if total_available < quantity_needed:
                raise ValueError(
                    f"Not enough stock. Available: {total_available}"
                )

            remaining = quantity_needed
            total_amount = unit_price * quantity_needed

            cur.execute(
                "INSERT INTO sales (user_id, total_amount, status) VALUES (%s, %s, %s)",
                (user_id, total_amount, "completed"),
            )
            sale_id = cur.lastrowid

            for batch in batches:
                if remaining == 0:
                    break

                batch_id = batch[0]
                batch_quantity = batch[1]
                quantity_to_sell = min(remaining, batch_quantity)

                cur.execute(
                    "UPDATE batches SET quantity = quantity - %s WHERE id = %s",
                    (quantity_to_sell, batch_id),
                )
                cur.execute(
                    """
                    INSERT INTO sale_items
                    (sale_id, batch_id, medicine_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (sale_id, batch_id, medicine_id, quantity_to_sell, unit_price),
                )


                remaining -= quantity_to_sell

            conn.commit()
            return {
                "sale_id": sale_id,
                "medicine": medicine_name,
                "quantity": quantity_needed,
                "total_amount": total_amount,
            }

        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
