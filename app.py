from flask import Flask, render_template, session, render_template_string, request, redirect
import sqlite3
from datetime import date, timedelta, datetime

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
DB_PATH = "Databases/good_food.db"

UPLOAD_FOLDER = "static/images"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, image FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

@app.route("/")
def index():
    products = get_products()
    return render_template("index.html", products=products)

@app.route("/checkout", methods=["POST"])
def checkout():
    products = get_products()
    quantities = {item: int(request.form.get("product_" +item, 0)) for item,_,_ in products}
    filtered = {k: v for k, v in quantities.items() if v > 0}
    if not filtered:
        return redirect("/")
    summary = ", ".join(f"{k} ({v})" for k, v in filtered.items())
    total = 0
    receipt = []
    for name, price,_ in products:
        qty = filtered.get(name)
        if qty:
            line_total=  qty*price
            receipt.append((name,qty,line_total))
            total+=line_total
        
    timestamp = datetime.today().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (date, products, total) VALUES (?, ?, ?)", (timestamp, summary, total))
    conn.commit()
    conn.close()
    return render_template("/gracias.html", receipt = receipt, total = total)

@app.route("/products")
def product_manager():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("products.html", products=products)
from pathlib import Path
@app.route("/update", methods=["POST"])
def update_prods():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    i = request.form.get('id')
    name = request.form.get(f'name')
    price = request.form.get(f'price')
    image = request.files.get(f'image')

    if image and image.filename:
        filename = secure_filename(image.filename)
        save_path = Path(UPLOAD_FOLDER)/ filename
        image.save(str(save_path))
    else:
        save_path = ''
    c.execute("UPDATE products SET name = ?, price = ?, image = ? WHERE id  = ?", (name, price, str(save_path), i))
    conn.commit()
    conn.close()
    return redirect("/products")

@app.route("/products/delete", methods=["POST"])
def delete_product():
    name = request.form["name"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return redirect("/products")

@app.route("/products/add", methods=["POST"])
def add_product():
    name = request.form["name"]
    price = float(request.form["price"])
    image = request.files.get("image")
    if image and image.filename:
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER,filename)
        image.save(image_path)
    else:
        image_path = ""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price, image) VALUES (?, ?, ?)", (name, price, image_path))
    conn.commit()
    conn.close()
    return redirect("/products")



app.secret_key = "f92e4b9c638a82e82d1e4e9b4753d1a9fabc1cd2e279c6e7f291f083e82c9b91"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == "chrisjamesortiz":
            session["is_admin"] = True
            return redirect("/")
        else:
            return render_template("admin.html", error="Wrong password")
    return render_template("admin.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/chart")
def chart():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    start = request.args.get("start")
    end =  request.args.get("end") or date.today()

    offset = request.args.get("offset",50)
    if not start:
        start = end - timedelta(days=7)
    

    start_full = f"{str(start)} 00:00:00"
    end_full = f"{str(end)} 23:59:59"

    length = c.execute("select count(*) from orders where date between ? and ?",(start_full, end_full)).fetchone()[0]

    c.execute("Select id, date, products, total from orders where date between ? and ? Limit  ?", (start_full,end_full,offset))
   
    data = c.fetchall()
    
    c.execute("Select name, price from products")
    prod = c.fetchall()
    pdict = {name:price for name,price in prod}
    summ = {name: {'qty': 0, 'total': 0} for name, _ in prod}
    full_total = 0
    for _, _, items, total in data:
        for item in items.split(","):
            name, qty = item.strip().rsplit(' ',1)
            qty = int(qty[1])
            summ[name]['qty'] +=qty
            summ[name]['total']+=  pdict[name]
            full_total += pdict[name]
    conn.close()
    return render_template("chart.html", 
                           orders = data, 
                           full_total = full_total,
                           start = str(start),
                           end = str(end), 
                           summary = summ, 
                           length=length,
                           offset=offset)

@app.route("/del_order", methods = ["POST"])
def del_order():
    order_id = request.form.get('o_id')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("select * from orders")
    row= c.fetchall()
    c.execute("delete from orders where id = ?", (order_id,))

    conn.commit()
    conn.close()
    return redirect("/chart")

# @app.route("/test")
# def test():
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute("SELECT name, price, image FROM products")
#     products = cursor.fetchall()
#     conn.close()
#     return render_template("test.html",products = products)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5000)

