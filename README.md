# 🏪 Role-Based Store Management System

A lightweight, secure, and console-based **Role-Based Access Control (RBAC)** Store Management System built with **Python** and **SQLite**. It streamlines inventory tracking, point-of-sale (POS) billing, user management, and sales reporting with strict role-level permissions.

---

## ✨ Features

* **Secure Authentication:** Uses `SHA-256` cryptographic hashing to securely store user passwords.
* **Role-Based Access Control (RBAC):** Three distinct user roles with tailored dashboards and permissions:
  * **Admin:** Full system access, including creating users (Managers/Cashiers), managing inventory, processing sales, and viewing total revenue reports.
  * **Manager:** Inventory control, including adding new products, updating stock levels, and checking inventory.
  * **Cashier:** Point-of-Sale (POS) access to process customer checkouts, automatically deduct sold stock, and view product availability.
* **Zero External Dependencies:** Powered entirely by Python's built-in `sqlite3`, `hashlib`, and `datetime` modules.
* **Auto-Initializing Database:** Automatically creates `store_management.db` and seeds a default administrator account on first launch.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Database:** SQLite3
* **Security:** SHA-256 Password Hashing (`hashlib`)

---

## 🚀 Getting Started

### Prerequisites
Make sure you have **Python 3.6+** installed on your machine. You can verify your installation by running:
```bash
python --version
```

### Installation & Running the App

1. **Clone the repository** (or download `store_system.py`):
   ```bash
   git clone https://github.com
   cd role-based-store-management
   ```

2. **Run the application:**
   ```bash
   python store_system.py
   ```

---

## 🔑 Default Credentials

On the first run, the system automatically generates a default **Admin** account:

* **Username:** `admin`
* **Password:** `admin123`

> **Note:** After logging in as Admin, use **Option 5** from the dashboard to create separate `manager` and `cashier` accounts for testing role restrictions.

---

## 📋 Role Permissions Matrix

| Feature / Action | Admin | Manager | Cashier |
| :--- | :---: | :---: | :---: |
| View Inventory | ✅ | ✅ | ✅ |
| Add New Product | ✅ | ✅ | ❌ |
| Update Product Stock | ✅ | ✅ | ❌ |
| Process Sale (POS) | ✅ | ❌ | ✅ |
| Create Users (Manager/Cashier) | ✅ | ❌ | ❌ |
| View Sales & Revenue Report | ✅ | ❌ | ❌ |

---

## 🗄️ Database Schema

The application automatically creates three relational tables inside `store_management.db`:

* **`users`**: Stores `id`, `username`, `password` (hashed), and `role` (`admin`, `manager`, `cashier`).
* **`products`**: Stores `id`, `name`, `price`, and `stock`.
* **`sales`**: Tracks `id`, `product_id`, `quantity`, `total_price`, `sold_by`, and `sale_date`.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to fork this repository and submit a pull request.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
