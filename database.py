import sqlite3

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Пользователи
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER,
    balance REAL DEFAULT 0
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
    price INTEGER,
    product_id INTEGER,
    status TEXT
)
""")

conn.commit()


def add_user(user_id, referrer_id=None):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)",
        (user_id, referrer_id)
    )
    conn.commit()


def add_product(currency, amount, price):
    cursor.execute(
        "INSERT INTO products (currency, amount, price) VALUES (?, ?, ?)",
        (currency, amount, price)
    )
    conn.commit()


def get_products(currency):
    cursor.execute(
        "SELECT * FROM products WHERE currency=? ORDER BY id DESC",
        (currency,)
    )
    return cursor.fetchall()


def get_all_products():
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    return cursor.fetchall()


def get_product(product_id):
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    return cursor.fetchone()


def delete_product(product_id):
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    return cursor.rowcount  # сколько строк удалили (0 или 1)


def create_order(user_id, price, product_id):
    cursor.execute(
        "INSERT INTO orders (user_id, price, product_id, status) VALUES (?, ?, ?, ?)",
        (user_id, price, product_id, "pending")
    )
    conn.commit()
    return cursor.lastrowid



