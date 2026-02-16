import sqlite3

# важно для серверов/потоков
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Пользователи
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

# Товары
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency TEXT,
    amount TEXT,
    price INTEGER
)
""")

# Заказы
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    price INTEGER,
    status TEXT
)
""")

conn.commit()


def add_user(user_id: int):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def add_product(currency: str, amount: str, price: int):
    cursor.execute(
        "INSERT INTO products (currency, amount, price) VALUES (?, ?, ?)",
        (currency, amount, price)
    )
    conn.commit()


def delete_product(product_id: int):
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()


def get_products(currency: str):
    cursor.execute("SELECT * FROM products WHERE currency=? ORDER BY id DESC", (currency,))
    return cursor.fetchall()


def get_all_products():
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    return cursor.fetchall()


def get_product(product_id: int):
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    return cursor.fetchone()


def create_order(user_id: int, product_id: int, price: int):
    cursor.execute(
        "INSERT INTO orders (user_id, product_id, price, status) VALUES (?, ?, ?, ?)",
        (user_id, product_id, price, "pending")
    )
    conn.commit()
    return cursor.lastrowid


def get_pending_orders():
    cursor.execute("SELECT * FROM orders WHERE status='pending' ORDER BY id DESC")
    return cursor.fetchall()


def update_order_status(order_id: int, status: str):
    cursor.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()


def get_order(order_id: int):
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    return cursor.fetchone()


