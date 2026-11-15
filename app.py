import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

DB_NAME = "store_rbac_v2.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class DatabaseManager:
    def _init_(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_tables()
        self.seed_admin()

    def setup_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
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
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                sold_by TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def seed_admin(self):
        admin_pass = hash_password("admin123")
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", admin_pass, "admin")
        )
        self.conn.commit()

db = DatabaseManager()

st.set_page_config(page_title="Role-Based Store Management", layout="wide")
st.title("🏪 Role-Based Store Management System")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.subheader("🔐 লগইন করুন")
    with st.form("login_form"):
        username = st.text_input("Username (ডিফল্ট: admin)")
        password = st.text_input("Password (ডিফল্ট: admin123)", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            db.cursor.execute(
                "SELECT role FROM users WHERE username = ? AND password = ?",
                (username, hash_password(password))
            )
            user = db.cursor.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user[0]
                st.rerun()
            else:
                st.error("ভুল ইউজারনেম বা পাসওয়ার্ড!")
else:
    st.sidebar.success(f"ইউজার: {st.session_state.username} ({st.session_state.role.upper()})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    role = st.session_state.role
    menu = ["📦 স্টক দেখুন", "🛒 পণ্য বিক্রি (Sales)"]
    if role in ["admin", "manager"]:
        menu.append("➕ নতুন পণ্য / স্টক আপডেট")
        menu.append("📊 বিক্রির রিপোর্ট")
    if role == "admin":
        menu.append("👥 ইউজার ম্যানেজমেন্ট")

    choice = st.sidebar.radio("মেনু নির্বাচন করুন", menu)

    if choice == "📦 স্টক দেখুন":
        
        st.subheader("বর্তমান পণ্যের তালিকা")
        df = pd.read_sql_query("SELECT id, name AS 'পণ্যের নাম', price AS 'দাম', stock AS 'স্টক' FROM products", db.conn)
        st.dataframe(df, use_container_width=True)

    elif choice == "🛒 পণ্য বিক্রি (Sales)":
        st.subheader("নতুন বিক্রি (Billing)")
        products = db.cursor.execute("SELECT name, price, stock FROM products WHERE stock > 0").fetchall()
        if not products:
         st.warning("স্টকে কোনো পণ্য নেই।")
        else:
            prod_dict = {p[0]: (p[1], p[2]) for p in products}
            selected_prod = st.selectbox("পণ্য সিলেক্ট করুন", list(prod_dict.keys()))
            price, max_stock = prod_dict[selected_prod]
            qty = st.number_input("পরিমাণ", min_value=1, max_value=max_stock, value=1)
            st.info(f"মোট বিল: {price * qty} টাকা")
            if st.button("বিক্রি নিশ্চিত করুন"):
                db.cursor.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (qty, selected_prod))
                db.cursor.execute(
                    "INSERT INTO sales (product_name, quantity, total_price, sold_by, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (selected_prod, qty, price * qty, st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                db.conn.commit()
                st.success("বিক্রি সফল হয়েছে!")
                st.rerun()

    elif choice == "➕ নতুন পণ্য / স্টক আপডেট":
        st.subheader("নতুন পণ্য যোগ বা স্টক আপডেট")
        with st.form("add_product"):
            p_name = st.text_input("পণ্যের নাম")
            p_price = st.number_input("দাম", min_value=0.0, step=1.0)
            p_stock = st.number_input("স্টক সংখ্যা", min_value=1, step=1)
            if st.form_submit_button("সেভ করুন") and p_name:
                db.cursor.execute("SELECT id FROM products WHERE name = ?", (p_name,))
                if db.cursor.fetchone():
                    db.cursor.execute("UPDATE products SET price = ?, stock = stock + ? WHERE name = ?", (p_price, p_stock, p_name))
                else:
                    db.cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (p_name, p_price, p_stock))
                db.conn.commit()
                st.success("পণ্য আপডেট হয়েছে!")

    elif choice == "📊 বিক্রির রিপোর্ট":
        st.subheader("সকল বিক্রির হিসাব")
        sales_df = pd.read_sql_query("SELECT * FROM sales ORDER BY id DESC", db.conn)
        st.dataframe(sales_df, use_container_width=True)

    elif choice == "👥 ইউজার ম্যানেজমেন্ট":
        st.subheader("নতুন স্টাফ বা ম্যানেজার তৈরি করুন")
        with st.form("add_user"):
            new_user = st.text_input("নতুন Username")
            new_pass = st.text_input("Password", type="password")
            new_role = st.selectbox("Role নির্বাচন করুন", ["cashier", "manager", "admin"])
            if st.form_submit_button("ইউজার তৈরি করুন") and new_user and new_pass:
                try:
                    db.cursor.execute(
                        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (new_user, hash_password(new_pass), new_role)
                    )
                    db.conn.commit()
                    st.success(f"{new_user} ({new_role}) তৈরি হয়েছে!")
                except sqlite3.IntegrityError:
                    st.error("এই ইউজারনেমটি আগে থেকেই আছে!")
