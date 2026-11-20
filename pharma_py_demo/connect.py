import mysql.connector

def connect():
    return mysql.connector.connect(
        host="mysql-32193cf5-alustudent-4f14.j.aivencloud.com",
        user="avnadmin",       # use a limited application account, not root
        password="AVNS_fiK9RqMnb1XhsD7T5iT",
        database="defaultdb",
        autocommit=False,        # transactions are controlled by the program
    )

def record_sale(conn, items, customer_name=None):
    """items is a list of (batch_id, quantity). Returns the new sale_id."""
    if not items or any(qty <= 0 for _, qty in items):
        raise ValueError("Each item needs a quantity greater than zero.")

    cur = conn.cursor()
    try:
        conn.start_transaction()
        cur.execute("INSERT INTO sales (customer_name) VALUES (%s)", (customer_name,))
        sale_id = cur.lastrowid

        for batch_id, qty in items:
            # Lock the batch while we read its price and save the line.
            cur.execute(
                """SELECT m.selling_price
                   FROM batches AS b
                   JOIN medicines AS m ON m.medicine_id = b.medicine_id
                   WHERE b.batch_id = %s
                   FOR UPDATE""",
                (batch_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Batch {batch_id} does not exist.")

            cur.execute(
                """INSERT INTO sale_items (sale_id, batch_id, quantity, unit_price)
                   VALUES (%s, %s, %s, %s)""",
                (sale_id, batch_id, qty, row[0]),
            )

        conn.commit()
        return sale_id
    except Exception:
        conn.rollback()          # undo the sale header and every line
        raise
    finally:
        cur.close()