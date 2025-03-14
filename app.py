from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Flask App Initialization
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database Connection Function
def get_db_connection():
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home Page - Food Service Page
@app.route("/")
def index():
    products = [
        {"name": "Pizza", "price": 299, "image": "images/pizza.jpg"},
        {"name": "Burger", "price": 199, "image": "images/burger.jpg"},
        {"name": "Pasta", "price": 249, "image": "images/pasta.jpg"},
        {"name": "Sandwich", "price": 149, "image": "images/sandwich.jpg"},
        {"name": "Salad", "price": 99, "image": "images/salad.jpg"},
    ]
    return render_template("index.html", products=products)

# User Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists! Try another."
        finally:
            conn.close()
        return redirect(url_for("index"))
    return render_template("register.html")

# User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            return "Invalid username or password."
    return render_template("login.html")

# Cart Page
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cart_items = conn.execute("SELECT * FROM cart WHERE user_id = ?", (session["user_id"],)).fetchall()
    total_price = sum(item["total"] for item in cart_items)
    conn.close()

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

# Add Item to Cart
@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    product_name = request.form["product_name"]
    price = float(request.form["price"])
    quantity = int(request.form["quantity"])
    total = price * quantity
    user_id = session["user_id"]

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO cart (user_id, product_name, price, quantity, total) VALUES (?, ?, ?, ?, ?)",
        (user_id, product_name, price, quantity, total)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("cart"))

# Place Order
@app.route("/place-order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cart_items = conn.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,)).fetchall()

    for item in cart_items:
        conn.execute(
            "INSERT INTO orders (user_id, product_name, price, quantity, total) VALUES (?, ?, ?, ?, ?)",
            (user_id, item["product_name"], item["price"], item["quantity"], item["total"])
        )

    conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return "Order placed successfully! <a href='/'>Back to Shop</a>"

# Remove Item from Cart
@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cart_id = request.form["cart_id"]

    conn = get_db_connection()
    conn.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("cart"))

# Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("username") != "admin":
        return "Access Denied!"
    return render_template("admin_dashboard.html")

# View Users (Admin)
@app.route("/admin/users")
def view_users():
    if "user_id" not in session or session.get("username") != "admin":
        return "Access Denied!"

    conn = get_db_connection()
    users = conn.execute("SELECT user_id, username FROM users").fetchall()
    conn.close()
    return render_template("admin_users.html", users=users)

# View Orders (Admin)
@app.route("/admin/orders")
def view_orders():
    if "user_id" not in session or session.get("username") != "admin":
        return "Access Denied!"

    conn = get_db_connection()
    orders = conn.execute("""
        SELECT orders.order_id, users.username, orders.product_name, orders.price,
               orders.quantity, orders.total
        FROM orders
        JOIN users ON orders.user_id = users.user_id
    """).fetchall()
    conn.close()
    return render_template("admin_orders.html", orders=orders)

# Admin Reset Password
@app.route("/admin/reset-password", methods=["POST"])
def reset_password():
    if "user_id" not in session or session.get("username") != "admin":
        return "Access Denied!"

    user_id = request.form["user_id"]
    new_password = request.form["new_password"]
    hashed_password = generate_password_hash(new_password)

    conn = get_db_connection()
    conn.execute("UPDATE users SET password = ? WHERE user_id = ?", (hashed_password, user_id))
    conn.commit()
    conn.close()

    return "Password reset successfully! <a href='/admin/dashboard'>Back to Dashboard</a>"

if __name__ == "__main__":
    app.run(debug=True)
