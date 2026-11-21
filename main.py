from mysql.connector import Error 
from alerts_reports import AlertsAndReportsService
from auth import AuthService
from db import PharmaDatabase
from inventory import InventoryService
from sales import SalesService

class PharmaCLI:
    def __init__(self):
        self.db = PharmaDatabase()
        self.auth = AuthService(self.db)
        self.inventory = InventoryService(self.db)
        self.sales = SalesService(self.db)
        self.reports = AlertsAndReportsService(self.db)
        self.current_user = None

    def login_loop(self):
        for _ in range(3):
            print("\n=== PHARMA LOGIN ===")
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            user = self.auth.login(username, password)
            if user:
                self.current_user = user
                print(f"\nWelcome, {user['full_name']} ({user['role']})!")
                return True
            print("Invalid credentials or inactive account.")
        print("Too many failed login attempts.")
        return False

    def menu_loop(self):
        while self.current_user:
            role = self.current_user["role"]
            print("\n=== PHARMA MENU ===")
            print("1. Search medicines")
            print("2. Record FEFO sale")
            print("3. View expiry & low-stock alerts")
            if role == "pharmacist":
                print("4. Add medicine / batch")
                print("5. Today's sales summary")
                print("6. Void a sale")
                print("7. Create user")
            print("0. Logout / Exit")

            choice = input("\nChoose option: ").strip()
            try:
                if choice == "1":
                    kw = input("Search keyword (blank for all): ").strip()
                    for m in self.inventory.search_medicines(kw):
                        print(
                            f"[{m['id']}] {m['name']} | Stock: {m['sellable_qty']} | "
                            f"Status: {m['status']} | Price: {float(m['unit_price']):.2f} | "
                            f"Nearest Exp: {m['nearest_expiry'] or 'N/A'}"
                        )
                elif choice == "2":
                    med_id = int(input("Medicine ID: ").strip())
                    qty = int(input("Quantity to sell: ").strip())
                    receipt = self.sales.record_fefo_sale(med_id, qty, self.current_user["id"])
                    print(
                        f"Sale #{receipt['sale_id']} recorded! Total: {receipt['total_amount']:.2f}"
                    )
                    for a in receipt["allocations"]:
                        print(
                            f"  - Batch {a['batch_number']} (Exp {a['expiry_date']}): "
                            f"-{a['qty_taken']} ({a['remaining_in_batch']} left)"
                        )
                elif choice == "3":
                    print("\n-- Expiring Soon (<= 90 days) --")
                    for b in self.reports.get_expiring_soon():
                        print(
                            f"{b['medicine_name']} [{b['batch_number']}]: {b['quantity']} units "
                            f"| Exp {b['expiry_date']} ({b['days_left']}d left)"
                        )
                    print("\n-- Expired Stock --")
                    for b in self.reports.get_expired_batches():
                        print(
                            f"{b['medicine_name']} [{b['batch_number']}]: {b['quantity']} units "
                            f"| Expired {b['expiry_date']}"
                        )
                    print("\n-- Low / Out of Stock --")
                    for m in self.inventory.search_medicines(""):
                        if m["status"] in ("Low Stock", "Out of Stock"):
                            print(
                                f"{m['name']} [{m['status']}]: {m['sellable_qty']} "
                                f"(Reorder: {m['reorder_level']})"
                            )
                elif choice == "4" and role == "pharmacist":
                    name = input("Medicine name: ").strip()
                    batch_no = input("Batch number: ").strip()
                    qty = int(input("Quantity: ").strip())
                    price = float(input("Unit price: ").strip())
                    exp = input("Expiry date (YYYY-MM-DD): ").strip()
                    reorder = int(input("Reorder level [20]: ").strip() or "20")
                    _, batch_id = self.inventory.add_medicine_and_batch(
                        name, batch_no, qty, price, exp, reorder
                    )
                    print(f"Saved batch #{batch_id} for {name}.")
                elif choice == "5" and role == "pharmacist":
                    summary = self.reports.today_sales_summary()
                    print(
                        f"Today's Sales: {summary['sales_count']} | "
                        f"Revenue: {float(summary['revenue']):.2f}"
                    )
                elif choice == "6" and role == "pharmacist":
                    sale_id = int(input("Sale ID to void: ").strip())
                    reason = input("Reason: ").strip()
                    self.sales.void_sale(sale_id, reason)
                    print(f"Sale #{sale_id} voided and batch quantities restored.")
                elif choice == "7" and role == "pharmacist":
                    uname = input("New username: ").strip()
                    fname = input("Full name: ").strip()
                    pwd = input("Password: ").strip()
                    urole = input("Role (pharmacist/attendant) [attendant]: ").strip() or "attendant"
                    uid = self.auth.create_user(uname, fname, pwd, urole)
                    print(f"Created user #{uid} ({uname}).")
                elif choice == "0":
                    print("Goodbye!")
                    self.current_user = None
                else:
                    print("Invalid choice for your role.")
            except ValueError as err:
                print(f"Input/Rule error: {err}")
            except Error as db_err:
                print(f"Database error: {db_err}")

def main():
    try:
        cli = PharmaCLI()
        if cli.login_loop():
            cli.menu_loop()
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()