import sqlite3 as sql
import os

DB = "Databases/good_food.db"

co = sql.connect(DB)
c = co.cursor()


c.execute('''Create table if not exists products_new (id integer primary key  autoincrement, name text not null, price int not null, image text)''')

c.execute("insert into products_new (name,price,image) select name, price, image from products")

c.execute('drop table products;')

c.execute('alter table products_new Rename to products')


co.commit()
co.close()
