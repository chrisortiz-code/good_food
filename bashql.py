import sqlite3 as sql

con = sql.connect("Databases/good_food.db")
c = con.cursor()

# c.execute("Alter table products add column image text;")

c.execute("delete from orders")

# Add 'position' column if it doesn't exist
try:
    c.execute("ALTER TABLE products ADD COLUMN position INTEGER")
except sql.OperationalError:
    # Column already exists
    pass

# Set position = id + 1 for all existing products where position is NULL or 0
c.execute("UPDATE products SET position = id + 1 WHERE position IS NULL OR position = 0")

con.commit()