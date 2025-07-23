from flask import Flask, render_template, session, render_template_string, request, redirect
import sqlite3
from datetime import date, timedelta, datetime
from pathlib import Path
import os
from werkzeug.utils import secure_filename
import re


app = Flask(__name__)
DB_PATH = "Databases/good_food.db"

UPLOAD_FOLDER = "static/images"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, image FROM products ORDER BY position ASC, id ASC")
    products = cursor.fetchall()
    conn.close()
    return products

def smart_capitalize(name):
    # Remove special characters except spaces and slashes
    name = re.sub(r'[^\w\s/]', ' ', name)
    def cap_word(word, is_first):
        if is_first or len(word) > 3:
            return word.capitalize()
        return word.lower()
    words = re.split(r'(\s+)', name)  # Keep spaces
    result = []
    first = True
    for w in words:
        if w.strip() == '':
            result.append(w)
        else:
            result.append(cap_word(w, first))
            if w.strip():
                first = False
    return ''.join(result).strip()

@app.route("/")
def index():
    products = get_products()
    return render_template("index.html", products=products)

@app.route("/checkout", methods=["POST"])
def checkout():
    products = get_products()
    quantities = {
        item: int(request.form.get("product_" + item, 0))
        for item, _, _ in products
    }

    filtered = {k: v for k, v in quantities.items() if v > 0}

    if not filtered:
        return redirect("/")

    order_items = []
    total = 0
    receipt = []

    for name, price, _ in products:
        qty = filtered.get(name)
        if qty:
            # New format: name:unit_price;qty
            order_items.append(f"{name}:{price};{qty}")

            line_total = qty * price
            receipt.append((name, qty, line_total))
            total += line_total

    products_string = ", ".join(order_items)
    timestamp = datetime.today().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (date, products, total) VALUES (?, ?, ?)",
        (timestamp, products_string, total)
    )
    conn.commit()
    conn.close()

    return render_template("/gracias.html", receipt=receipt, total=total)

@app.route("/products")
def product_manager():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image FROM products ORDER BY position ASC, id ASC")
    products = cursor.fetchall()
    conn.close()
    return render_template("products.html", products=products)



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
    name = smart_capitalize(name)
    import re
    raw_price = request.form.get('price', '').strip()
    if re.match(r'^-?\d+$', raw_price):
        try:
            price = int(raw_price)
        except ValueError:
            price = 0
    else:
        price = 0
    image = request.files.get("image")
    if image and image.filename:
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER,filename)
        image.save(image_path)
    else:
        image_path = ""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Get the current max position
    cursor.execute("SELECT MAX(position) FROM products")
    max_position = cursor.fetchone()[0]
    if max_position is None:
        new_position = 1
    else:
        new_position = max_position + 1
    cursor.execute("INSERT INTO products (name, price, image, position) VALUES (?, ?, ?, ?)", (name, price, image_path, new_position))
    conn.commit()
    conn.close()
    return redirect("/products")

@app.route("/products/bulk_update", methods=["POST"])
def bulk_update_products():
    from werkzeug.utils import secure_filename
    import re
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get all product ids from the form
    ids = request.form.getlist('id')
    names = request.form.getlist('name')
    prices = request.form.getlist('price')
    positions = request.form.getlist('position')
    # For file uploads, use request.files.getlist for all images
    images = request.files.getlist('image')
    for idx, prod_id in enumerate(ids):
        name = names[idx]
        name = smart_capitalize(name)
        raw_price = prices[idx].strip()
        if re.match(r'^-?\d+$', raw_price):
            try:
                price = int(raw_price)
            except ValueError:
                price = 0
        else:
            price = 0
        position = int(positions[idx]) if positions[idx].isdigit() else idx + 1
        image = images[idx] if idx < len(images) else None
        # Handle image upload or keep existing
        if image and image.filename:
            filename = secure_filename(image.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(save_path)
            image_path = save_path
        else:
            c.execute("SELECT image FROM products WHERE id = ?", (prod_id,))
            current_image = c.fetchone()
            image_path = current_image[0] if current_image else ''
        c.execute("UPDATE products SET name = ?, price = ?, image = ?, position = ? WHERE id = ?", (name, price, image_path, position, prod_id))
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
@app.route("/logout", methods = ["POST"])
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
    summ = {}
    full_total = 0

    for _, _, items, _ in data:
        for item in items.split(","):
            item = item.strip()
            if not item:
                continue

            # Expect format: Name:Price;Qty
            try:
                name_price, qty = item.split(";",1)
                name, price = name_price.split(":",1)
                name = name.strip()
                price = int(price.strip())
                qty = int(qty.strip())

                # Fallback if name missing (shouldn’t happen with new format)
                if not name:
                    name = "Other"

                if name not in summ:
                    summ[name] = {'qty': 0, 'total': 0}

                summ[name]['qty'] += qty
                summ[name]['total'] += price * qty
                full_total += price * qty

            except Exception as e:
                print(f"⚠️ Skipped malformed item: {item} ({e})")

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

@app.route("/test")
def test():
    return render_template("test.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5000)

