import sqlite3 as sql

import random 
import string


db = "Databases/good_food.db"


co = sql.connect(db)
c = co.cursor()

c.execute("drop table orders")

c.execute('select name from products')

names = [row[0] for row in c.fetchall()]
c.execute("create table orders (id integer primary key autoincrement, date date not null, products text not null, total int not null)")

for i in range(60):
    date = "2025-06-28"
    items = random.choice(names)+ " (5)"
    total = 500
    c.execute('insert into orders (date,products,total) values (?,?,?)',(date,items,total))

co.commit()
