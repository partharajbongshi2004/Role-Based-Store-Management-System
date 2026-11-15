import hashlib
import sqlite3
from datetime import datetime

DB_NAME = "store_rbac_v2.db"


class DatabaseManager:

  def __init__(self, db_name=DB_NAME):
    self.conn = sqlite3.connect(db_name)
    self.cursor = self.conn.cursor()
    self.setup_tables()
    self.seed_admin()

  def setup_tables(self):
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'cashier'))
            )
        """)
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)
    self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER,
                total_price REAL,
                sold_by TEXT,
                sale_date TEXT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
    self.conn.commit()

  def hash_password(self, password):
    return hashlib.sha256(password.encode()).hexdigest()

  def seed_admin(self):
    admin_pass = self.hash_password("admin123")
    try:
      self.cursor.execute(
          "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
          ("admin", admin_pass, "admin"),
      )
      self.conn.commit()
    except sqlite3.IntegrityError:
      pass


class StoreSystem:

  def __init__(self):
    self.db = DatabaseManager()
    self.current_user = None
    self.current_role = None

  def login(self):
    print("\n--- STORE MANAGEMENT SYSTEM LOGIN ---")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    hashed_pw = self.db.hash_password(password)

    self.db.cursor.execute(
        "SELECT username, role FROM users WHERE username = ? AND password = ?",
        (username, hashed_pw),
    )
    user = self.db.cursor.fetchone()

    if user:
      self.current_user, self.current_role = user
      print(
          f"\nWelcome, {self.current_user}! Logged in as:"
          f" [{self.current_role.upper()}]"
      )
      return True
    else:
      print("\n[ERROR] Invalid username or password!")
      return False

  # --- ADMIN FUNCTIONS ---
  def create_user(self):
    if self.current_role != "admin":
      print("[ACCESS DENIED] Only Admins can create new users.")
      return
    username = input("New Username: ").strip()
    password = input("Password: ").strip()
    role = input("Assign Role (manager / cashier): ").strip().lower()

    if role not in ["manager", "cashier"]:
      print("[ERROR] Role must be either 'manager' or 'cashier'.")
      return

    try:
      hashed_pw = self.db.hash_password(password)
      self.db.cursor.execute(
          "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
          (username, hashed_pw, role),
      )
      self.db.conn.commit()
      print(f"[SUCCESS] User '{username}' ({role}) has been created.")
    except sqlite3.IntegrityError:
      print("[ERROR] This username already exists.")

  def view_sales_report(self):
    if self.current_role != "admin":
      print("[ACCESS DENIED] Only Admins can view sales reports.")
      return
    self.db.cursor.execute("""
            SELECT s.id, p.name, s.quantity, s.total_price, s.sold_by, s.sale_date 
            FROM sales s JOIN products p ON s.product_id = p.id
        """)
    rows = self.db.cursor.fetchall()
    print("\n--- SALES REPORT ---")
    total_revenue = 0.0
    if not rows:
      print("No sales recorded yet.")
    for r in rows:
      print(
          f"Sale ID: {r[0]} | Product: {r[1]} | Qty: {r[2]} | Total:"
          f" ${r[3]:.2f} | Sold By: {r[4]} | Date: {r[5]}"
      )
      total_revenue += r[3]
    print(f"\nTotal Revenue: ${total_revenue:.2f}")
    print("-" * 50)

  # --- ADMIN & MANAGER FUNCTIONS ---
  def add_product(self):
    if self.current_role not in ["admin", "manager"]:
      print("[ACCESS DENIED] You do not have permission to add products.")
      return
    name = input("Product Name: ").strip()
    try:
      price = float(input("Unit Price ($): "))
      stock = int(input("Initial Stock Quantity: "))
      if price < 0 or stock < 0:
        print("[ERROR] Price and stock cannot be negative.")
        return
      self.db.cursor.execute(
          "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
          (name, price, stock),
      )
      self.db.conn.commit()
      print(f"[SUCCESS] '{name}' added to inventory.")
    except ValueError:
      print("[ERROR] Price and stock must be valid numbers.")
    except sqlite3.IntegrityError:
      print("[ERROR] A product with this name already exists.")

  def update_stock(self):
    if self.current_role not in ["admin", "manager"]:
      print("[ACCESS DENIED] You do not have permission to update stock.")
      return
    self.view_inventory()
    try:
      prod_id = int(input("Enter Product ID to restock: "))
      add_qty = int(input("Enter quantity to add: "))
      if add_qty <= 0:
        print("[ERROR] Quantity to add must be greater than zero.")
        return
      self.db.cursor.execute(
          "UPDATE products SET stock = stock + ? WHERE id = ?",
          (add_qty, prod_id),
      )
      if self.db.cursor.rowcount > 0:
        self.db.conn.commit()
        print("[SUCCESS] Stock updated successfully.")
      else:
        print("[ERROR] Product ID not found.")
    except ValueError:
      print("[ERROR] Please enter valid numeric values.")

  # --- ALL ROLES FUNCTIONS ---
  def view_inventory(self):
    self.db.cursor.execute("SELECT id, name, price, stock FROM products")
    products = self.db.cursor.fetchall()
    print("\n--- CURRENT INVENTORY ---")
    if not products:
      print("No products available in the store.")
    for p in products:
      print(
          f"ID: {p[0]} | Name: {p[1]} | Price: ${p[2]:.2f} | Stock: {p[3]} units"
      )
    print("-" * 50)

  # --- CASHIER & ADMIN FUNCTIONS ---
  def make_sale(self):
    if self.current_role not in ["admin", "cashier"]:
      print("[ACCESS DENIED] You do not have permission to process sales.")
      return
    self.view_inventory()
    try:
      prod_id = int(input("Enter Product ID to sell: "))
      qty = int(input("Enter Quantity: "))

      self.db.cursor.execute(
          "SELECT name, price, stock FROM products WHERE id = ?", (prod_id,)
      )
      product = self.db.cursor.fetchone()

      if not product:
        print("[ERROR] Product not found.")
        return

      name, price, stock = product
      if qty <= 0 or qty > stock:
        print(f"[ERROR] Insufficient stock! Available stock: {stock} units.")
        return

      total = price * qty
      sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      self.db.cursor.execute(
          "UPDATE products SET stock = stock - ? WHERE id = ?", (qty, prod_id)
      )
      self.db.cursor.execute(
          "INSERT INTO sales (product_id, quantity, total_price, sold_by,"
          " sale_date) VALUES (?, ?, ?, ?, ?)",
          (prod_id, qty, total, self.current_user, sale_date),
      )
      self.db.conn.commit()
      print(
          f"\n[RECEIPT] Sold {qty} x {name} | Total: ${total:.2f} | Thank you!"
      )
    except ValueError:
      print("[ERROR] Please enter valid numeric values.")

  def menu(self):
    while True:
      print(f"\n=== DASHBOARD ({self.current_role.upper()}) ===")
      print("1. View Inventory")

      if self.current_role in ["admin", "manager"]:
        print("2. Add New Product")
        print("3. Update Product Stock")

      if self.current_role in ["admin", "cashier"]:
        print("4. Process Sale (POS)")

      if self.current_role == "admin":
        print("5. Create New User (Manager/Cashier)")
        print("6. View Sales Report")

      print("0. Logout")

      choice = input("Select an option: ").strip()

      if choice == "1":
        self.view_inventory()
      elif choice == "2" and self.current_role in ["admin", "manager"]:
        self.add_product()
      elif choice == "3" and self.current_role in ["admin", "manager"]:
        self.update_stock()
      elif choice == "4" and self.current_role in ["admin", "cashier"]:
        self.make_sale()
      elif choice == "5" and self.current_role == "admin":
        self.create_user()
      elif choice == "6" and self.current_role == "admin":
        self.view_sales_report()
      elif choice == "0":
        print("Logged out successfully.")
        self.current_user = None
        self.current_role = None
        break
      else:
        print("[ERROR] Invalid option or unauthorized access.")


if __name__ == "__main__":
  app = StoreSystem()
  while True:
    if app.login():
      app.menu()
    again = input("\nDo you want to log in again? (y/n): ").strip().lower()
    if again != "y":
      print("Exiting Store Management System. Goodbye!")
      break
