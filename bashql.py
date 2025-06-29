import sqlite3 as sql

con = sql.connect("Databases/good_food.db")
c = con.cursor()

# c.execute("Alter table products add column image text;")

c.execute("delete from orders")

con.commit()