from flask import Flask, redirect, render_template, session, request, flash, url_for, jsonify, send_file, Response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import json
from flask_mail import Mail, Message    #pip install Flask-Mail
from io import BytesIO
from datetime import datetime, date
from decimal import Decimal
import re

app = Flask(__name__)

# MY SQL Configuration
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "rootpassword"
app.config['MYSQL_DB'] = "billing_software"
app.secret_key = "your_seceret_key"

mysql = MySQL(app)

# Mail config (example: Gmail SMTP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'   # sender email
app.config['MAIL_PASSWORD'] = 'your_app_password'      # Gmail app password
app.config['MAIL_DEFAULT_SENDER'] = ('MyPOS Contact', 'your_email@gmail.com')

mail = Mail(app)

# Landing or index page
@app.route('/')
def index():
    return render_template('index.html')

# Contact Page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method=='POST'):
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        try:
            msg = Message(
                subject=f"New Contact Form: {subject}",
                recipients=['receiver_email@example.com']  # where to send
            )
            msg.body = f"""
            You have received a new message from {name} <{email}>.

            Subject: {subject}

            Message:
            {message}
            """
            mail.send(msg)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            flash(f"Failed to send message. Error: {str(e)}", "danger")

        return redirect(url_for('contact'))

    return render_template('contact.html')

# About Us PAge
@app.route('/about-us')
def about_us():
    return render_template('about-us.html')

# Privacy Policy Page
@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

# Terms& Condition Page
@app.route('/terms&condition')
def terms_condition():
    return render_template('terms&condition.html')

# User Login Page
@app.route('/user-login', methods = ['GET', 'POST'])
def User_login():
    msg = ""
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('Select * from user where email=%s AND password=%s',(email,password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['users_id'] = user['id']
            msg = "Login Sucessfull!!!"
            return redirect('/user-dashboard')
        else:
            msg = "Login Failed!!!"
            return redirect('/user-login')

    return render_template('user-login.html')

# User Logout Page
@app.route('/user-logout')
def user_logout_page():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    return render_template('user-logout.html')

# User Logout Code
@app.route('/logout')
def logout():
    session.pop('users_id', None)
    session.pop('email', None)
    return redirect('/user-login')

# Admin Login Page
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("Select * from admin Where email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            msg = "Login successfull!!!"

            return redirect('/admin-dashboard')
        else:
            msg = "Your email or password not matched, Try again!!!"
            return redirect('/admin-login')

    return render_template('admin-login.html', msg=msg)

# Admin Logout Page
@app.route('/admin-logout')
def admin_logout():
   user_id = session.get('user_id')
   if not user_id:
        return redirect('/admin-login')
   return render_template('admin-logout.html') 

# Admin Logout Code
@app.route('/logout-account')
def admin_logout_code():
    session.pop('user_id', None)
    session.pop('email', None)
    return redirect('/admin-login')

# Admin Dashboard
@app.route('/admin-dashboard')
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id:  # user not logged in
        return redirect('/admin-login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Total Products
    cursor.execute('Select Count(id) As count From Product')
    total_product = cursor.fetchone()
    # Total Customers
    cursor.execute('Select Count(*) As count From customer')
    total_cust = cursor.fetchone()
    # Total Sales this year
    cursor.execute("""
            SELECT SUM(payable) AS sales
            FROM invoice
            WHERE YEAR(date) = YEAR(CURDATE())
        """)
    sales_this_year = cursor.fetchone()
    # Total Sales Last year
    cursor.execute("""
            SELECT SUM(payable) AS sales
            FROM invoice
            WHERE YEAR(date) = YEAR(CURDATE())-1
        """)
    sales_last_year = cursor.fetchone()

     # Recent Sales
    cursor.execute("""SELECT 
            i.date,
            i.payable AS amount,
            c.name AS customer_name
            FROM invoice i
            JOIN customer c ON i.customer_id = c.id
            ORDER BY i.date DESC Limit 5;
            """)
    recent_sales = cursor.fetchall()

        # Monthly sales Graph (last 12 months)
    cursor.execute(""" SELECT DATE_FORMAT(date, '%b') AS month, 
           SUM(payable) AS total_sales
            FROM invoice
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY YEAR(date), MONTH(date), DATE_FORMAT(date, '%b')
            ORDER BY YEAR(date), MONTH(date)
            """)
    monthly_sales_data = cursor.fetchall()

    monthly_sales_labels = [row['month'] for row in monthly_sales_data]           # ['Mar', 'Apr', 'May' ...]
    monthly_sales_values = [float(row['total_sales']) for row in monthly_sales_data]  # [5000, 8000, ...]


    cursor.close()

    return render_template('admin-dashboard.html', total_product=total_product, total_cust=total_cust, sales_this_year=sales_this_year, sales_last_year=sales_last_year, monthly_sales_labels=monthly_sales_labels, monthly_sales_values=monthly_sales_values, recent_sales=recent_sales)

# Admin Sales PAge
@app.route('/admin-sales')
def admin_sales():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Show All Invoices in Sales Page
    cursor.execute("""
        SELECT i.*, c.name as customer_name 
        FROM invoice i
        LEFT JOIN customer c ON i.customer_id=c.id
        ORDER BY i.id DESC
    """)
    invoices = cursor.fetchall()

    # Total Monthly Sales
    cursor.execute("""SELECT 
            YEAR(date) AS year,
            MONTH(date) AS month,
            SUM(payable) AS total_sales
            FROM invoice
            GROUP BY YEAR(date), MONTH(date)
            ORDER BY year, month
    """)
    sales_monthly = cursor.fetchone()

    # Last Year Total Sales
    cursor.execute("""SELECT 
            YEAR(date) AS year,
            SUM(payable) AS total_sales
            FROM invoice
            WHERE YEAR(date) = YEAR(CURDATE()) - 1
            GROUP BY YEAR(date);
            """)
    last_year_sales = cursor.fetchone()

    # Total Sales Today
    cursor.execute('Select Sum(payable) As total_sale From invoice where Date(date) = CURDATE()')
    today_sales = cursor.fetchone()

    # Total Bills Created this year
    cursor.execute("Select Count(*) as count From invoice Where DATE(date)>=DATE_FORMAT(CURDATE(), '%Y-%01-01')")
    total_bills = cursor.fetchone()

    # Recent Sales
    cursor.execute("""SELECT 
            i.date,
            i.payable AS amount,
            c.name AS customer_name
            FROM invoice i
            JOIN customer c ON i.customer_id = c.id
            ORDER BY i.date DESC Limit 5;
            """)
    recent_sales = cursor.fetchall()

    # Weekly sales (last 7 days, grouped by day)
    cursor.execute("""
        SELECT DATE(date) as sale_date, SUM(payable) as total_sale
        FROM invoice
        WHERE date >= CURDATE() - INTERVAL 7 DAY
        GROUP BY DATE(date)
        ORDER BY sale_date
    """)
    weekly_sales = cursor.fetchall()

    # Prepare labels & values for Chart.js
    labels = [row['sale_date'].strftime("%a") for row in weekly_sales]  # Mon, Tue...
    values = [float(row['total_sale']) for row in weekly_sales]

    cursor.close()
        
    return render_template('admin-sales.html', invoices=invoices,labels=labels,values=values, sales_monthly=sales_monthly, today_sales=today_sales, total_bills=total_bills, last_year_sales=last_year_sales, recent_sales=recent_sales)

# Admin Report PAge
@app.route('/admin-report')
def admin_report():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Total Sales This Month
    cursor.execute("Select Sum(payable) As total_sale From invoice where Date(date) >= DATE_FORMAT(CURDATE(), '%Y-%M-01')")
    month_sales = cursor.fetchone()

    # Count Unpaid bills 
    cursor.execute("Select Count(*) As count From invoice Where status='unpaid'")
    unpaid_bills = cursor.fetchone()

    # New Customer added in this month
    cursor.execute("""SELECT 
        COUNT(*) AS added
        FROM customer
        WHERE MONTH(date) = MONTH(CURRENT_DATE())
        AND YEAR(date) = YEAR(CURRENT_DATE());
        """)
    new_cust = cursor.fetchone()

    #Total Product Sold So Far
    cursor.execute("""SELECT SUM(ii.qty) AS sold
        FROM invoice_item ii
        JOIN invoice i ON ii.invoice_id = i.id
        WHERE MONTH(i.date) = MONTH(CURRENT_DATE())
        AND YEAR(i.date) = YEAR(CURRENT_DATE());
        """)
    sold_product = cursor.fetchone()

    # Monthly sales Graph (last 12 months)
    cursor.execute("""
    SELECT DATE_FORMAT(date, '%b') AS month, 
           SUM(payable) AS total_sales
    FROM invoice
    WHERE date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
    GROUP BY YEAR(date), MONTH(date), DATE_FORMAT(date, '%b')
    ORDER BY YEAR(date), MONTH(date)
    """)
    monthly_sales_data = cursor.fetchall()

    monthly_sales_labels = [row['month'] for row in monthly_sales_data]           # ['Mar', 'Apr', 'May' ...]
    monthly_sales_values = [float(row['total_sales']) for row in monthly_sales_data]  # [5000, 8000, ...]
  
    # Top selling products (sum qty from invoice_item)
    cursor.execute("""
        SELECT p.name, SUM(ii.qty) as total_qty
        FROM invoice_item ii
        JOIN product p ON ii.product_id = p.id
        GROUP BY ii.product_id
        ORDER BY total_qty DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()

    # Example: Monthly Sales
    cursor.execute("""
        SELECT 
            YEAR(i.date) AS year,
            MONTH(i.date) AS month,
            SUM(ii.qty * ii.unit_price) AS total_sales,
            COUNT(DISTINCT i.customer_id) AS customers,
            SUM(ii.qty) AS products_sold
        FROM invoice i
        JOIN invoice_item ii ON i.id = ii.invoice_id
        GROUP BY YEAR(i.date), MONTH(i.date)
        ORDER BY year, month
    """)
    sales_data = cursor.fetchall()

    product_labels = [row['name'] for row in top_products]
    product_values = [int(row['total_qty']) for row in top_products]


    cursor.close()
    return render_template('admin-report.html', month_sales=month_sales, sold_product=sold_product, new_cust=new_cust,  unpaid_bills=unpaid_bills,
                           monthly_sales_labels=monthly_sales_labels,
                           monthly_sales_values=monthly_sales_values,
                           product_labels=product_labels,
                           product_values=product_values,
                           sales_data=sales_data)

def default_serializer(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()  # Convert datetime/date → string
    elif isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal → float
    elif isinstance(obj, bytes):
        return obj.decode("utf-8")  # Convert bytes → string
    return str(obj)  # Fallback: convert anything else to string

# Admin Report Download all Data 
@app.route('/backup/download')
def download_backup():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    tables = ["admin", "user", "customer", "product", "invoice", "invoice_item", "payment"]
    backup_data = {}

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        backup_data[table] = cursor.fetchall()

    cursor.close()

    json_data = json.dumps(backup_data, indent=4, default=default_serializer)

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=backup.json"}
    )

# Admin Report Upload All Backup Data
@app.route('/backup/upload', methods=['POST'])
def upload_backup():
    try:
        file = request.files['file']
        if not file:
            return "No file uploaded", 400

        data = json.load(file)

        cursor = mysql.connection.cursor()

        # Restore admin
        for a in data['admin']:
            cursor.execute("INSERT INTO admin (id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
                        (a['id'], a['name'], a['email'], a['password'], a['role']))

        # Restore product
        for p in data['product']:
            cursor.execute("INSERT INTO product (id, name, sku, hsn_sac, unit, gst_rate, unit_price, stock_qty, is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (p['id'], p['name'], p['sku'], p['hsn_sac'], p['unit'], p['gst_rate'], p['unit_price'], p['stock_qty'], p['is_active']))

        # Restore users
        for u in data['user']:
            cursor.execute("INSERT INTO user (id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
                        (u['id'], u['name'], u['email'], u['password'], u['role']))

        # Restore customers
        for c in data['customer']:
            cursor.execute("INSERT INTO customer (id, name, phone, email, state, city) VALUES (%s,%s,%s,%s,%s,%s)",
                        (c['id'], c['name'], c['phone'], c['email'], c['state'], c['city']))

        # Restore invoice
        for i in data['invoice']:
            cursor.execute("INSERT INTO invoice (id, date, customer_id, place_of_supply, subtotal, discount_amount, cgst, sgst, igst, round_off, grand_total, status, user_id, discount, payable) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (i['id'], i['date'], i['customer_id'], i['place_of_supply'], i['subtotal'], i['discount_amount'], i['cgst'], i['sgst'], i['igst'], i['round_off'], i['grand_total'], i['status'], i['user_id'], i['discount'], i['payable']))

        # Restore invoice_item
        for i in data['invoice_item']:
            cursor.execute("INSERT INTO invoice_item (id, invoice_id, product_id, description, qty, unit_price, discount_pct, gst_rate, line_subtotal, line_cgst, line_sgst, line_igst, line_total, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (i['id'], i['invoice_id'], i['product_id'], i['description'], i['qty'], i['unit_price'], i['discount_pct'], i['gst_rate'], i['line_subtotal'], i['line_cgst'], i['line_sgst'], i['line_igst'], i['line_total'], i['created_at'], i['updated_at']))

        # Restore payment
        for i in data['payment']:
            cursor.execute("INSERT INTO payment (id, invoice_id, amount, method, paid_at, created_at, updated_at ) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (i['id'], i['invoice_id'], i['amount'], i['method'], i['paid_at'], i['created_at'], i['updated_at']))

        mysql.connection.commit()
        cursor.close()
    except:
        return redirect('/data_exist')
    return "Backup restored successfully!"

@app.route('/data_exist')
def uploaded_data_exists():
    return render_template("uploaded_data_exists.html")

# Admin Product Page
@app.route('/admin-product', methods = ['GET', 'POST'])
def admin_product():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')
    
    msg = None
    # --- ADD PRODUCT (this form posts to /admin-product) ---
    if request.method == "POST":
        name = request.form['productName']
        sku = request.form['sku']
        hsn_sac = request.form['hsn_sac']
        units = request.form['units']
        gst = request.form['gst']
        price = request.form['price']
        stock = request.form['stock']
        active = request.form.get('active',0)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('Insert Into product(name, sku, hsn_sac, unit, gst_rate, unit_price, stock_qty, is_active) Values(%s, %s, %s, %s, %s, %s, %s, %s)',(name, sku, hsn_sac, units, gst, price, stock, active))
        mysql.connection.commit() 
        cursor.close()
        msg = "✅ Product added successfully!"

    # fetch all products for listing
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Select * From Product')
    mysql.connection.commit()
    products = cursor.fetchall()   # <-- This gets the actual rows (list of dicts)   # ✅ fetch all rows
    cursor.close()    

    return render_template('admin-product.html', msg=msg, products=products, single_product=None)

# Load same page but with one product prefilled in the Edit form
@app.route('/admin-product/<int:id>', methods=['GET'])
def get_single_product(id):
    user_id = session['user_id']
    if not user_id:
        return redirect('/admin-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM product WHERE id = %s', (id,))
    single_product = cursor.fetchone()
    cursor.close()

     # you MUST also pass products because the page lists them
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM product')
    products = cur.fetchall()
    cur.close()

    return render_template('admin-product.html', products=products ,single_product=single_product)

# Admin Delete Product 
@app.route('/delete-product/<int:id>')
def delete_product(id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('Delete From product Where id = %s', (id,))
        mysql.connection.commit()
        cursor.close()
        return redirect('/admin-product')
    except Exception as e:
        return redirect('/product-not-delete')

# If the product is used in invoice atleast once then admin can not delete the product, so redirect admin to this page
@app.route('/product-not-delete')
def product_not_delete():
    return render_template('product_not_delete.html')

# Admin Delete Admin 
@app.route('/delete-admin/<int:id>')
def delete_admin(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Delete From admin Where id=%s', (id,))
    mysql.connection.commit()
    cursor.close()
    return redirect('/admin-setting')

# Admin Delete User Credentials
@app.route('/delete-user/<int:id>')
def delete_user(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Delete From user Where id=%s', (id,))
    mysql.connection.commit()
    cursor.close()
    return redirect('/admin-setting')

# Admin Update Products
@app.route('/update-product/<int:id>', methods=['POST'])
def edit_product(id):
    user_id = session['user_id']
    if not user_id:
        return redirect('/login')

    name = request.form['productName']
    sku = request.form['sku']
    hsn_sac = request.form['hsn_sac']
    units = request.form['units']
    gst = request.form['gst']
    price = request.form['price']
    stock = request.form['stock']
    active = request.form.get('active',0)

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(''' Update Product 
                    Set name = %s, sku = %s, hsn_sac = %s, unit = %s, gst_rate = %s, unit_price = %s, stock_qty = %s, is_active = %s 
                    where id = %s''', (name, sku, hsn_sac, units, gst, price, stock, active ,id,)
                    )
    mysql.connection.commit()
    cursor.close()
    return redirect('/admin-product')
    
# Admin Customer PAge
@app.route('/admin-customer', methods=['GET', 'POST'])
def admin_customer():
   user_id = session.get('user_id')
   if not user_id:
        return redirect('/admin-login')
   
   if request.method == 'POST':
       name = request.form['name']
       phone = request.form['phone']
       email = request.form['email']
       gender = request.form['gender']
       gstin = request.form['gstin']
       address = request.form['address']
       country = request.form['country']
       state = request.form['state']
       city = request.form['city']

       cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
       cursor.execute(''' Insert Into customer(name, phone, email, gender, gstin, address, country, state, city)
                    Value(%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''',(name, phone, email, gender, gstin, address, country, state, city))


   cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
   cursor.execute('Select * From customer')
   customers = cursor.fetchall()
   # Total Sales This Month
   cursor.execute("Select Sum(payable) As total_sale From invoice where Date(date) >= DATE_FORMAT(CURDATE(), '%Y-%M-01')")
   month_sales = cursor.fetchone()

   # Total purchase of all customers
   cursor.execute("""SELECT 
    c.id AS customer_id,
    c.name AS cust_name,
    c.phone,
    c.email,
    c.city,
    IFNULL(SUM(i.payable), 0) AS total_purchase
    FROM customer c
    LEFT JOIN invoice i 
       ON c.id = i.customer_id
    GROUP BY c.id, c.name, c.phone, c.email, c.city
    ORDER BY total_purchase DESC;
    """)
   cust_total_purchase = cursor.fetchall()
   
   cursor.execute('Select Count(id) As count From customer')
   total_cust = cursor.fetchone()

   # Customers in last 30 days
   cursor.execute("""
        SELECT COUNT(*) AS last30days 
        FROM customer 
        WHERE date >= (NOW() - INTERVAL 30 DAY)
    """)
   last30days = cursor.fetchone()['last30days']
   mysql.connection.commit()
   cursor.close()
#    print(total_cust)
   return render_template('admin-customer.html', customers=customers, total_cust=total_cust, last30days=last30days, cust_total_purchase=cust_total_purchase, month_sales=month_sales)
    
# Admin Setting Page
@app.route('/admin-setting', methods=['GET','POST'])
def admin_setting():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('Insert Into admin(name, email, password) Value(%s, %s, %s)',(name, email, password))
        mysql.connection.commit()
        cursor.close()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Select * From admin where id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.execute('Select * from admin')
    admins = cursor.fetchall()
    cursor.execute('Select * from user')
    pos_users = cursor.fetchall()
    cursor.close()
    
    return render_template('admin-setting.html', user=user, admins=admins, pos_users=pos_users)

# Admin Setting for change or update the email and password
@app.route('/admin-setting/<int:id>', methods=['POST'])
def change_email_pass(id):
    email = request.form['editemail']
    password = request.form['editpassword']
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(''' Update admin
                   Set email=%s, password=%s
                   Where id=%s''', (email, password, id))
    mysql.connection.commit()
    cursor.close()
    return redirect('/admin-setting')

# Admin Setting Add USers
@app.route('/admin-setting/add-user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cursor  = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Insert Into user(name, email, password) Value(%s, %s, %s)', (name, email, password))
    mysql.connection.commit()
    cursor.close()
    return redirect('/admin-setting') 

# User Dashboard PAge
@app.route('/user-dashboard')
def user_dashboard():
    users_id = session.get('users_id')
    if not users_id:        
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Select * from user where id=%s', (users_id,))
    user = cursor.fetchone()
    cursor.execute('Select Count(id) As count From customer')
    total_cust = cursor.fetchone()
    cursor.execute('Select Count(id) As count From product')
    total_product = cursor.fetchone()
    cursor.execute('Select Count(id) As count From invoice')
    total_bill = cursor.fetchone()
    cursor.execute('select sum(payable) As sales from invoice;')
    total_sales = cursor.fetchone()

     # Fetch invoices with customer names
    cursor.execute("""
        SELECT i.id, i.date, i.payable, i.status, c.name as customer_name
        FROM invoice i
        JOIN customer c ON i.customer_id = c.id
        ORDER BY i.date DESC
    """)
    invoices = cursor.fetchall()

    # Fetch sales data for last 30 days
    cursor.execute("""
        SELECT DATE(date) as day, SUM(payable) as total
        FROM invoice
        WHERE date >= CURDATE() - INTERVAL 30 DAY
        GROUP BY DATE(date)
        ORDER BY day
    """)
    sales_data = cursor.fetchall()
    cursor.close()

    # Prepare data for Chart.js
    labels = [row["day"].strftime("%d %b") for row in sales_data]
    values = [float(row["total"]) for row in sales_data]

    return render_template('user-dashboard.html', user=user, total_cust=total_cust, total_product=total_product, total_bill=total_bill, total_sales=total_sales,
        invoices=invoices,
        labels=labels,
        values=values)

# User Product Page
@app.route('/user-product')
def user_product():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
     # fetch all products for listing
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('Select * From Product')
    mysql.connection.commit()
    products = cursor.fetchall()   # <-- This gets the actual rows (list of dicts)   # ✅ fetch all rows
    cursor.close()   
    return render_template('user-product.html', products=products)

# User Customer Page
@app.route('/user-customer', methods=['GET', 'POST'])
def user_customer():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    if request.method == 'POST':
       name = request.form['name']
       phone = request.form['phone']
       email = request.form['email']
       gender = request.form['gender']
       gstin = request.form['gstin']
       address = request.form['address']
       country = request.form['country']
       state = request.form['state']
       city = request.form['city']

       cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
       cursor.execute(''' Insert Into customer(name, phone, email, gender, gstin, address, country, state, city)
                    Value(%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''',(name, phone, email, gender, gstin, address, country, state, city))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    mysql.connection.commit()
    cursor.execute('Select * From customer')
    customers = cursor.fetchall()
    # mysql.connection.commit()
    cursor.close()
    return render_template('user-customer.html', customers=customers)

# User Setting PAge
@app.route('/user-setting')
def user_setting():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # cursor.execute('Select * From user')
    # user = cursor.fetchone()
    cursor.execute('Select * from user where id=%s', (users_id,))
    user = cursor.fetchone()
    cursor.close()
    return render_template('user-setting.html', user=user)

# User Setting Update USer's Credentials
@app.route('/user-setting/<int:id>', methods=['POST'])
def update_user_setting(id):
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(''' Update user
                   Set name=%s, email=%s, password=%s
                   Where id=%s''', (name, email, password, id))
        mysql.connection.commit()
        cursor.close()
    return redirect('/user-setting')

# USer Sales Page
@app.route('/user-sales')
def user_sales():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT i.*, c.name as customer_name 
        FROM invoice i
        LEFT JOIN customer c ON i.customer_id=c.id
        ORDER BY i.id DESC
    """)
    invoices = cursor.fetchall()
    # Total Sales Today
    cursor.execute('Select Sum(payable) As total_sale From invoice where Date(date) = CURDATE()')
    today_sales = cursor.fetchone()
    # Total Sales This week
    cursor.execute('Select Sum(payable) As total_sale From invoice where Date(date) >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)')
    this_week_sales = cursor.fetchone()
    # Total Sales This Month
    cursor.execute("Select Sum(payable) As total_sale From invoice where Date(date) >= DATE_FORMAT(CURDATE(), '%Y-%M-01')")
    month_sales = cursor.fetchone()
    # Total sales this year
    cursor.execute("Select Sum(payable) As total_sale From invoice where Date(date) >= DATE_FORMAT(CURDATE(), '%Y-01-01')")
    year_sales = cursor.fetchone()
    # Total Unpaid bills
    cursor.execute("Select Count(*) As count From invoice Where status='unpaid'")
    unpaid_bills = cursor.fetchone()
    # Weekly sales (last 7 days, grouped by day)
    cursor.execute("""
        SELECT DATE(date) as sale_date, SUM(payable) as total_sale
        FROM invoice
        WHERE date >= CURDATE() - INTERVAL 7 DAY
        GROUP BY DATE(date)
        ORDER BY sale_date
    """)
    weekly_sales = cursor.fetchall()

    # Prepare labels & values for Chart.js
    labels = [row['sale_date'].strftime("%a") for row in weekly_sales]  # Mon, Tue...
    values = [float(row['total_sale']) for row in weekly_sales]

    # Top selling products (sum qty from invoice_item)
    cursor.execute("""
        SELECT p.name, SUM(ii.qty) as total_qty
        FROM invoice_item ii
        JOIN product p ON ii.product_id = p.id
        GROUP BY ii.product_id
        ORDER BY total_qty DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()

    product_labels = [row['name'] for row in top_products]
    product_values = [int(row['total_qty']) for row in top_products]
    cursor.close()
    return render_template('user-sales.html', invoices=invoices, today_sales=today_sales, this_week_sales=this_week_sales, month_sales=month_sales, year_sales=year_sales, unpaid_bills=unpaid_bills,
                           labels=labels,
                           values=values,
                           product_labels=product_labels,
                           product_values=product_values)

# User Report PAge
@app.route('/user-report')
def user_report():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Total new Customer this year
    cursor.execute("Select Count(*) as count From customer Where DATE(date)>=DATE_FORMAT(CURDATE(), '%Y-%01-01')")
    new_cust = cursor.fetchone()
    # Total Bills Created this year
    cursor.execute("Select Count(*) as count From invoice Where DATE(date)>=DATE_FORMAT(CURDATE(), '%Y-%01-01')")
    total_bills = cursor.fetchone()
    # Total Sales this year
    cursor.execute("""
            SELECT SUM(payable) AS sales
            FROM invoice
            WHERE YEAR(date) = YEAR(CURDATE())
            """)

    total_sales = cursor.fetchone()

        # Total Sales Last year
    cursor.execute("""
            SELECT SUM(payable) AS sales
            FROM invoice
            WHERE YEAR(date) = YEAR(CURDATE())-1
        """)
    sales_last_year = cursor.fetchone()

    
    # All Invoices
    cursor.execute("""
        SELECT i.*, c.name as customer_name 
        FROM invoice i
        LEFT JOIN customer c ON i.customer_id=c.id
        ORDER BY i.id DESC
    """)
    invoices = cursor.fetchall()
    
    # Weekly sales (last 7 days, grouped by day)
    cursor.execute("""
        SELECT DATE(date) as sale_date, SUM(payable) as total_sale
        FROM invoice
        WHERE date >= CURDATE() - INTERVAL 7 DAY
        GROUP BY DATE(date)
        ORDER BY sale_date
    """)
    weekly_sales = cursor.fetchall()

    # Prepare labels & values for Chart.js
    labels = [row['sale_date'].strftime("%a") for row in weekly_sales]  # Mon, Tue...
    values = [float(row['total_sale']) for row in weekly_sales]

    # Monthly sales (last 12 months)
    cursor.execute("""
    SELECT DATE_FORMAT(date, '%b') AS month, 
           SUM(payable) AS total_sales
    FROM invoice
    WHERE date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
    GROUP BY YEAR(date), MONTH(date), DATE_FORMAT(date, '%b')
    ORDER BY YEAR(date), MONTH(date)
    """)


    monthly_sales_data = cursor.fetchall()

    monthly_sales_labels = [row['month'] for row in monthly_sales_data]           # ['Mar', 'Apr', 'May' ...]
    monthly_sales_values = [float(row['total_sales']) for row in monthly_sales_data]  # [5000, 8000, ...]
    
    cursor.close()
    return render_template('user-report.html', new_cust=new_cust, invoices=invoices, total_bills=total_bills, total_sales=total_sales, sales_last_year=sales_last_year,
                           labels=labels,
                           values=values,
                           monthly_sales_labels=monthly_sales_labels,
                           monthly_sales_values=monthly_sales_values)

# -------------------------------
#  Dashboard - list invoices
# -------------------------------
@app.route('/admin-invoice')
def invoice():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT i.*, c.name as customer_name 
        FROM invoice i
        LEFT JOIN customer c ON i.customer_id=c.id
        ORDER BY i.id DESC
    """)
    invoices = cursor.fetchall()
    cursor.close()
    return render_template('admin_invoice_list.html', invoices=invoices)

# Look Out Invoice by id
@app.route('/admin/invoice/<int:invoice_id>')
def admin_view_invoice(invoice_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch invoice + customer
    cursor.execute(""" SELECT i.*,
                    c.name as customer_name, c.phone, c.email, c.address FROM invoice i
                    LEFT JOIN customer c 
                   ON i.customer_id=c.id WHERE i.id=%s """, [invoice_id])
    invoice = cursor.fetchone()
    # Fetch items
    cursor.execute("SELECT * FROM invoice_item WHERE invoice_id=%s", [invoice_id]) 
    items = cursor.fetchall() 

    cursor.close() 
    return render_template('admin_invoice_view.html', invoice=invoice, items=items)

# -------------------------------
#  Create Invoice Page
# -------------------------------
@app.route('/invoice/create', methods=['GET', 'POST'])
def create_invoice():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch customers and only active products with stock > 0
    cursor.execute("SELECT * FROM customer Order By name Asc")
    customers = cursor.fetchall()

    cursor.execute("SELECT * FROM product WHERE is_active=1 AND stock_qty > 0")
    products = cursor.fetchall()

    if request.method == "POST":
        customer_id = request.form['customer_id']
        place_of_supply = request.form['place_of_supply']
        status = request.form['status']
        payment_method = request.form['payment_method']

        # Insert invoice record
        cursor.execute("""
            INSERT INTO invoice(customer_id, place_of_supply, status)
            VALUES (%s, %s, %s)
        """, (customer_id, place_of_supply, status))
        invoice_id = cursor.lastrowid

        # Get line items
        product_ids = request.form.getlist('product_id[]')
        qtys = request.form.getlist('qty[]')
        discounts = request.form.getlist('discount[]')

        # Totals
        subtotal = total_cgst = total_sgst = total_igst = grand_total = 0

        for i in range(len(product_ids)):
            pid = int(product_ids[i])
            qty = float(qtys[i])
            discount_pct = float(discounts[i]) if discounts[i] else 0

            # Fetch product info
            cursor.execute("SELECT * FROM product WHERE id=%s", [pid])
            product = cursor.fetchone()

            unit_price_inclusive = float(product['unit_price'])
            gst_rate = float(product['gst_rate'])

            # Price after discount
            price_after_discount = unit_price_inclusive * qty
            discount_amount = price_after_discount * (discount_pct / 100)
            price_after_discount -= discount_amount

            # Base price (exclusive of GST)
            base_price = price_after_discount / (1 + gst_rate / 100)

            # Taxes
            if place_of_supply == "MP":  # intrastate
                line_cgst = (price_after_discount - base_price) / 2
                line_sgst = (price_after_discount - base_price) / 2
                line_igst = 0
            else:  # interstate
                line_cgst = 0
                line_sgst = 0
                line_igst = price_after_discount - base_price

            line_subtotal = base_price
            line_total = price_after_discount

            # Update totals
            subtotal += line_subtotal
            total_cgst += line_cgst
            total_sgst += line_sgst
            total_igst += line_igst
            grand_total += line_total

            # Insert invoice_item
            cursor.execute("""
                INSERT INTO invoice_item(invoice_id, product_id, description, qty, unit_price,
                discount_pct, gst_rate, line_subtotal, line_cgst, line_sgst, line_igst, line_total)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                invoice_id, pid, product['name'], qty, unit_price_inclusive, discount_pct, gst_rate,
                line_subtotal, line_cgst, line_sgst, line_igst, line_total
            ))

            # 🔻 Reduce stock from product table
            cursor.execute("""
                UPDATE product 
                SET stock_qty = stock_qty - %s
                WHERE id = %s AND stock_qty >= %s
            """, (qty, pid, qty))

            if cursor.rowcount == 0:
                mysql.connection.rollback()
                flash(f"Not enough stock for product {product['name']}", "danger")
                return redirect('/invoice/create')

        # Get grand discount
        grand_discount_pct = float(request.form.get('grand_discount'))
        grand_discount_amt = grand_total * (grand_discount_pct / 100)
        payable_total = grand_total - grand_discount_amt

        # Update invoice totals
        cursor.execute("""
            UPDATE invoice 
            SET subtotal=%s, cgst=%s, sgst=%s, igst=%s, grand_total=%s, discount=%s, payable=%s
            WHERE id=%s
        """, (subtotal, total_cgst, total_sgst, total_igst, grand_total, grand_discount_amt, payable_total, invoice_id))

        # Insert payment
        cursor.execute("""
            INSERT INTO payment(invoice_id, amount, method)
            VALUES (%s, %s, %s)
        """, (invoice_id, payable_total, payment_method))


        mysql.connection.commit()
        cursor.close()
        flash("Invoice created and stock updated successfully", "success")
        return redirect('/user-invoice-view')

    cursor.close()
    return render_template('create_invoice.html', customers=customers, products=products)

# Search customer While creating Inovice
@app.route("/search-customer")
def search_customer():
    term = request.args.get("term")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT id, name, phone, state FROM customer WHERE name LIKE %s LIMIT 10", 
        (f"%{term}%",)
    )
    results = cursor.fetchall()
    cursor.close()

    # Send state also
    suggestions = [
        {
            "id": r["id"],
            "label": f"{r['name']} ({r['phone']})",
            "value": r["name"],
            "state": r["state"],
            "phone": r["phone"]
        }
        for r in results
    ]
    return jsonify(suggestions)

# User Invoice View Page
@app.route('/user-invoice-view')
def user_invoice_view():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT i.*, c.name as customer_name 
        FROM invoice i
        LEFT JOIN customer c ON i.customer_id=c.id
        ORDER BY i.id DESC
    """)
    invoices = cursor.fetchall()
    cursor.close()
    
    return render_template('user-invoice-view.html', invoices=invoices)

# -------------------------------
#  View Particular Invoice
# -------------------------------
@app.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch invoice + customer
    cursor.execute(""" SELECT i.*,
                    c.name as customer_name, c.phone, c.email, c.address FROM invoice i
                    LEFT JOIN customer c 
                   ON i.customer_id=c.id WHERE i.id=%s """, [invoice_id])
    invoice = cursor.fetchone()
    # Fetch items
    cursor.execute("SELECT * FROM invoice_item WHERE invoice_id=%s", [invoice_id]) 
    items = cursor.fetchall() 

    cursor.close() 
    return render_template('invoice_view.html', invoice=invoice, items=items)

# Update Status to paid to unpaid and unpaid to paid (FOR USERS ONLY)
@app.route('/user/update/status/<int:id>')
def user_update_status(id):
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("Select status From invoice Where id=%s", (id,))
    inv_status = cursor.fetchone()
    
    if(inv_status['status'] == 'paid'):
        cursor.execute("UPDATE invoice SET status = 'unpaid' WHERE id=%s", (id,))
    else:
        cursor.execute("UPDATE invoice SET status = 'paid' WHERE id=%s", (id,))
        
    mysql.connection.commit()
    cursor.close()
    return redirect('/user-invoice-view')

# Update Status to paid to unpaid and unpaid to paid (FOR ADMIN ONLY)
@app.route('/admin/update/status/<int:id>')
def admin_update_status(id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("Select status From invoice Where id=%s", (id,))
    inv_status = cursor.fetchone()
    
    if(inv_status['status'] == 'paid'):
        cursor.execute("UPDATE invoice SET status = 'unpaid' WHERE id=%s", (id,))
    else:
        cursor.execute("UPDATE invoice SET status = 'paid' WHERE id=%s", (id,))
        
    mysql.connection.commit()
    cursor.close()
    return redirect('/admin-invoice')

# User Unpaid Invoices List PAge
@app.route('/user/unpaid-invoice')
def user_unpaid_bills():
    users_id = session.get('users_id')
    if not users_id:
        return redirect('/user-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT i.*, c.name as customer_name 
        FROM invoice i
        LEFT JOIN customer c ON i.customer_id=c.id
        where status!='paid'
        ORDER BY i.id DESC
    """)
    unpaid_bills = cursor.fetchall()
    cursor.close()
    return render_template('user-unpaid-bills.html', unpaid_bills=unpaid_bills)

# Admin Unpaid Invoice List Page
@app.route('/admin/unpaid-invoice')
def admin_unpaid_bills():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/admin-login')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("Select * From invoice where status!='paid'")
    unpaid_bills = cursor.fetchall()
    cursor.close()
    return render_template('admin-unpaid-bills.html', unpaid_bills=unpaid_bills)

# Handle 404 error
@app.errorhandler(404)
def page_not_found(e):
    # You can render a custom HTML template
    return render_template('404_error.html'), 404

# Run this file 
if __name__ == "__main__":
    app.run(debug = True)
