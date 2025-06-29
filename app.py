from flask import Flask, render_template, request, redirect
import sqlite3
import datetime

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
DB_PATH = "Databases/good_food.db"

UPLOAD_FOLDER = "images"

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
    quantities = {item: int(request.form.get(item, 0)) for item,_,_ in products}
    filtered = {k: v for k, v in quantities.items() if v > 0}
    if not filtered:
        return redirect("/")
    summary = ", ".join(f"{k} ({v})" for k, v in filtered.items())
    total = 0
    for name, qty in quantities.items():
        for pname, price, _ in products:
            if pname==name:
                total+=price * qty
                break
    timestamp = datetime.datetime.today().strftime("%Y-%m-%d %H:%M")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (date, products, total) VALUES (?, ?, ?)", (timestamp, summary, total))
    conn.commit()
    conn.close()
    return render_template("/gracias.html")

@app.route("/products")
def product_manager():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("products.html", products=products)

@app.route("/products/update", methods=["POST"])
def update_product():
    name = request.form["name"]
    price = float(request.form["price"])
    new_name = request.form["new_name"]
    
    image = request.files.get("image")

    if image and image.filename:
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER,filename)
        image.save(image_path)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ?, price = ?, image = ? WHERE name = ?", (new_name, price, image, name))
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price, image) VALUES (?, ?, ?)", (name, price, image_path))
    conn.commit()
    conn.close()
    return redirect("/products")

@app.route("/chart")
def chart():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("Select date, products, total from orders order by date")
    data = c.fetchall()
    print(data)
    conn.close()
    return render_template("chart.html", orders = data)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5000)