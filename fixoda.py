import sqlite3 as sql

DB = "Databases/good_food.db"
DEFAULT_PRICE = 50

co = sql.connect(DB)
c = co.cursor()

# Get current product prices
c.execute("SELECT name, price FROM products")
product_prices = {name: price for name, price in c.fetchall()}

# Read all old orders
c.execute("SELECT id, date, products, total FROM orders")
old_orders = c.fetchall()

# Create new orders table
c.execute("DROP TABLE IF EXISTS orders_new")
c.execute("""
    CREATE TABLE orders_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        products TEXT NOT NULL,
        total INT NOT NULL
    )
""")

for order_id, date, products_str, total in old_orders:
    new_items = []
    for item in products_str.split(","):
        item = item.strip()
        if not item:
            continue
        # Example: Apple (2)
        if "(" in item and ")" in item:
            name, qty = item.rsplit("(", 1)
            name = name.strip()
            qty = int(qty.replace(")", "").strip())

            unit_price = product_prices.get(name, DEFAULT_PRICE)
            new_items.append(f"{name}:{unit_price};{qty}")

    new_products_str = ", ".join(new_items)

    c.execute("""
        INSERT INTO orders_new (id, date, products, total)
        VALUES (?, ?, ?, ?)
    """, (order_id, date, new_products_str, total))

# Drop old table and rename
c.execute("DROP TABLE orders")
c.execute("ALTER TABLE orders_new RENAME TO orders")

co.commit()
co.close()

print("✅ Orders migration complete!")
