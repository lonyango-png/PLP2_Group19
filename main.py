from pathlib import Path 
import os
from mysql.connector import Error 
from alerts_reports import AlertsAndReportsService
from auth import AuthService
from db import PharmaDatabase
from inventory import InventoryService
from sales import SalesService


def load_env_file(env_path=".env"):
    """Load simple KEY=VALUE pairs from a .env file into os.environ."""
    path = Path(env_path)
    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
class PharmaCLI:
    def __init__(self):
        self.db = PharmaDatabase()
        self.auth = AuthService(self.db)
        self.inventory = InventoryService(self.db)
        self.sales = SalesService(self.db)
        self.reports = AlertsAndReportsService(self.db)
        self.current_user = None

    @staticmethod
    def _input_int(prompt):
        val = input(prompt).strip()
        if not val.lstrip('-').isdigit():
            raise ValueError(f"Expected a whole number, got '{val}'.")
        return int(val)

    @staticmethod
    def _input_float(prompt):
        val = input(prompt).strip()
        try:
            return float(val)
        except ValueError:
            raise ValueError(f"Expected a number, got '{val}'.")

    @staticmethod
    def _input_str(prompt):
        val = input(prompt).strip()
        if not val:
            raise ValueError(f"'{prompt.strip()}' cannot be empty.")
        return val

    @staticmethod
    def _input_date(prompt):
        val = input(prompt).strip()
        from datetime import datetime
        try:
            datetime.strptime(val, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date '{val}'. Use YYYY-MM-DD format.")
        return val

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
                print("8. Delete user")
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
                    med_id = self._input_int("Medicine ID: ")
                    qty = self._input_int("Quantity to sell: ")
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
                    name = self._input_str("Medicine name: ")
                    batch_no = self._input_str("Batch number: ")
                    qty = self._input_int("Quantity: ")
                    price = self._input_float("Unit price: ")
                    exp = self._input_date("Expiry date (YYYY-MM-DD): ")
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
                    sale_id = self._input_int("Sale ID to void: ")
                    reason = self._input_str("Reason: ")
                    self.sales.void_sale(sale_id, reason)
                    print(f"Sale #{sale_id} voided and batch quantities restored.")
                elif choice == "7" and role == "pharmacist":
                    uname = self._input_str("New username: ")
                    fname = self._input_str("Full name: ")
                    pwd = self._input_str("Password: ")
                    urole = input("Role (pharmacist/attendant) [Default: attendant]: ").strip() or "attendant"
                    uid = self.auth.create_user(uname, fname, pwd, urole)
                    print(f"Created user #{uid} ({uname}).")
                elif choice == "8" and role == "pharmacist":
                    for u in self.auth.list_users():
                        status = "active" if u["is_active"] else "inactive"
                        print(f"  {u['id']}. {u['username']} | {u['full_name']} | {u['role']} | {status}")
                    uname = self._input_str("Username to delete: ")
                    self.auth.delete_user(uname)
                    print(f"User '{uname}' deleted.")
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
    load_env_file()
    try:
        cli = PharmaCLI()
        if cli.login_loop():
            cli.menu_loop()
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()