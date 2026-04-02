from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

products = {
    "nature": {
        "name": "Eclipse of Grace",
        "price": 7500,
        "image": "images/angel.jpeg"
    },
    "midnight": {
        "name": "Midnight Guardian",
        "price": 8500,
        "image": "images/midnight.jpeg"
    }
}


# ---------- DATABASE ----------

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # users table
    cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')

    # orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        item TEXT,
        name TEXT,
        phone TEXT,
        address TEXT,
        payment TEXT,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()

# call function
init_db()
# ---------- HOME ----------
@app.route('/')
def home():
    return redirect('/dashboard')

# ---------- SIGNUP ----------

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing = cursor.fetchone()

        if existing:
            return "User already exists ❌"

        cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')   # inside IF

    return render_template('signin.html')   # outside IF but inside function

# ---------- LOGIN ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            session['cart'] = []

            # ADMIN CHECK
            if username.lower() == "admin":
                return redirect('/admin')
            else:
                return redirect('/dashboard')

        else:
            return "Invalid username or password ❌"

    return render_template('login.html')

# ---------- DASHBOARD ----------

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', username=session.get('user'))

# ---------- BUY ----------
@app.route('/buy/<item>', methods=['GET', 'POST'])
def buy(item):
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        payment = request.form['payment']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO orders (username, item, name, phone, address, payment, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session['user'], item, name, phone, address, payment, "Pending"))

        conn.commit()
        conn.close()

        return redirect('/success')

    return render_template('checkout.html', item=item)
   # ----------CART----------
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = 0

    for item in cart_items:
        total += item['price']

    return render_template('cart.html', cart=cart_items, total=total)

# -----add_to_cart----

@app.route('/add_to_cart/<item>')
def add_to_cart(item):

    if 'user' not in session:   # 👈 ADD THIS
        return redirect(url_for('login'))

    if 'cart' not in session:
        session['cart'] = []

    product = products.get(item)

    if product:
        session['cart'].append(product)
        session.modified = True

    return redirect(url_for('dashboard'))

#------checkout route---------
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        return redirect('/login')

    cart_items = session.get('cart', [])

    if not cart_items:
        return redirect('/cart')

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        payment = request.form['payment']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        for item in cart_items:
            cursor.execute("""
            INSERT INTO orders (username, item, name, phone, address, payment, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session['user'], item, name, phone, address, payment, "Pending"))

        conn.commit()
        conn.close()

        session['cart'] = []   # clear cart after order

        return redirect('/success')

    return render_template('checkout.html')

#  ----------succes rooute--------
@app.route('/success')
def success():
    return render_template('success.html')

# ---------- LOGOUT ----------

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('cart', None)
    return redirect('/')

# --------REMOVE BUTTON-----
@app.route('/remove/<item>')
def remove(item):
    if 'user' not in session:
        return redirect('/login')

    if 'cart' in session and item in session['cart']:
        session['cart'].remove(item)
        session.modified = True

    return redirect('/cart')

#--------orders viewing ------

@app.route('/orders')
def orders():
    # 🔐 check login
    if 'user' not in session:
        return redirect('/login')

    # 🔐 allow only admin
    if session['user'] != 'admin':
        return "Access Denied ❌"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()

    conn.close()

    return render_template('orders.html', orders=orders)

# -------My order page--------

@app.route('/my_orders')
def my_orders():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE username=?", (session['user'],))
    orders = cursor.fetchall()

    conn.close()

    return render_template('my_orders.html', orders=orders)

# ---------- ADMIN PANEL ----------
@app.route('/admin')
def admin():
    if 'user' not in session or session['user'].lower() != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()

    return render_template('allorders.html', orders=orders)



# -------ship-id-------------

@app.route('/ship/<int:id>')
def ship(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Shipped' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# --------deliver-id-------

@app.route('/deliver/<int:id>')
def deliver(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Delivered' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ---------- RUN ----------

if __name__ == "__main__":
    app.run(debug=True)
