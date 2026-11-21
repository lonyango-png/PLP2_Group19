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