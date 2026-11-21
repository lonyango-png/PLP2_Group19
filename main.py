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