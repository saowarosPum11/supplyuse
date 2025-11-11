from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
from datetime import datetime
import sqlite3
import os
import base64
import io
import xlsxwriter
from functools import wraps

def generate_document_no(conn, doc_type='IN'):
    c = conn.cursor()
    now = datetime.now()
    prefix = now.strftime('%y%m')
    
    # Get last document number for this month
    c.execute('SELECT document_no FROM stock_movements WHERE document_no LIKE ? ORDER BY document_no DESC LIMIT 1', 
              (f'{prefix}%',))
    result = c.fetchone()
    
    if result:
        last_no = result[0]
        running = int(last_no[-4:]) + 1
    else:
        running = 1
    
    return f'{prefix}{running:04d}'

app = Flask(__name__)
app.secret_key = 'wso_supply_key_2024'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('supply_inventory.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user[3]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Database setup
def init_db():
    conn = None
    try:
        conn = sqlite3.connect('supply_inventory.db')
        c = conn.cursor()
        
        # Products table
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            unit TEXT,
            min_stock INTEGER DEFAULT 0,
            current_stock INTEGER DEFAULT 0,
            image BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Add image column if it doesn't exist
        try:
            c.execute('ALTER TABLE products ADD COLUMN image BLOB')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add description column if it doesn't exist
        try:
            c.execute('ALTER TABLE products ADD COLUMN description TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add document_no column if it doesn't exist
        try:
            c.execute('ALTER TABLE stock_movements ADD COLUMN document_no TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Insert default users if not exists
        c.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                     ('admin', 'SupplyUse2024!', 'admin'))
        
        c.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('63010468',))
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                     ('63010468', '63010468', 'admin'))
        
        c.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('10008642',))
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                     ('10008642', '10008642', 'admin'))
        
        # Stock movements table
        c.execute('''CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            type TEXT CHECK(type IN ('IN', 'OUT')),
            quantity INTEGER,
            reference TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )''')
        
        conn.commit()
    finally:
        if conn:
            conn.close()

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/products')
@login_required
def products():
    init_db()  # Ensure database exists
    conn = None
    try:
        conn = sqlite3.connect('supply_inventory.db')
        c = conn.cursor()
        c.execute('SELECT id, name, barcode, unit, min_stock, current_stock, created_at FROM products ORDER BY name')
        products = c.fetchall()
        print(f"Found {len(products)} products")
        return render_template('products.html', products=products)
    finally:
        if conn:
            conn.close()

@app.route('/product_image/<int:product_id>')
def product_image(product_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT image FROM products WHERE id = ?', (product_id,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        from flask import Response
        return Response(result[0], mimetype='image/jpeg')
    else:
        return '', 404

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        barcode = request.form.get('barcode')
        unit = request.form.get('unit')
        description = request.form.get('description', '')
        min_stock = int(request.form.get('min_stock', 0))
        
        if 'image' in request.files and request.files['image'].filename:
            image_data = request.files['image'].read()
            c.execute('UPDATE products SET name=?, barcode=?, unit=?, description=?, min_stock=?, image=? WHERE id=?',
                     (name, barcode, unit, description, min_stock, image_data, product_id))
        else:
            c.execute('UPDATE products SET name=?, barcode=?, unit=?, description=?, min_stock=? WHERE id=?',
                     (name, barcode, unit, description, min_stock, product_id))
        
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = None
    try:
        conn = sqlite3.connect('supply_inventory.db')
        c = conn.cursor()
        c.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        return redirect(url_for('products'))
    finally:
        if conn:
            conn.close()

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        print(f"Form data received: {request.form}")
        print(f"Files received: {request.files}")
        
        init_db()  # Ensure database exists
        name = request.form.get('name', '').strip()
        barcode = request.form.get('barcode', '').strip()
        unit = request.form.get('unit', '').strip()
        description = request.form.get('description', '').strip()
        min_stock = int(request.form.get('min_stock', 0))
        
        print(f"Parsed data: name={name}, barcode={barcode}, unit={unit}, min_stock={min_stock}")
        
        if not name or not barcode or not unit:
            print("Validation failed: missing required fields")
            return render_template('add_product.html', error='กรุณากรอกข้อมูลให้ครบถ้วน')
        
        conn = None
        try:
            conn = sqlite3.connect('supply_inventory.db')
            c = conn.cursor()
            c.execute('INSERT INTO products (name, barcode, unit, description, min_stock) VALUES (?, ?, ?, ?, ?)',
                     (name, barcode, unit, description, min_stock))
            conn.commit()
            print(f"Product saved: {name}, {barcode}, {unit}, {min_stock}")
            return redirect(url_for('products'))
        except Exception as e:
            print(f"Error saving product: {e}")
            return render_template('add_product.html', error=f'เกิดข้อผิดพลาด: {e}')
        finally:
            if conn:
                conn.close()
    return render_template('add_product.html')

@app.route('/stock_in')
@login_required
def stock_in():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode FROM products ORDER BY name')
    products = c.fetchall()
    conn.close()
    return render_template('stock_in.html', products=products)

@app.route('/stock_in_list')
def stock_in_list():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('''SELECT sm.*, p.name, p.unit 
                FROM stock_movements sm 
                JOIN products p ON sm.product_id = p.id 
                WHERE sm.type = 'IN'
                ORDER BY sm.created_at DESC''')
    stock_ins = c.fetchall()
    conn.close()
    return render_template('stock_in_list.html', stock_ins=stock_ins)

@app.route('/stock_in_view/<int:movement_id>')
def stock_in_view(movement_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('''SELECT sm.*, p.name, p.unit 
                FROM stock_movements sm 
                JOIN products p ON sm.product_id = p.id 
                WHERE sm.id = ? AND sm.type = 'IN' ''', (movement_id,))
    movement = c.fetchone()
    
    c.execute('SELECT id, name FROM products ORDER BY name')
    products = c.fetchall()
    
    conn.close()
    
    if not movement:
        return redirect(url_for('stock_in_list'))
    
    # Check if document date is today or future
    doc_date = datetime.strptime(movement[6][:10], '%Y-%m-%d').date()
    today = datetime.now().date()
    can_edit = doc_date >= today
    
    return render_template('stock_in_view.html', movement=movement, products=products, can_edit=can_edit)

@app.route('/update_stock_in/<int:movement_id>', methods=['POST'])
def update_stock_in(movement_id):
    data = request.get_json()
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get current movement
    c.execute('SELECT * FROM stock_movements WHERE id = ?', (movement_id,))
    current = c.fetchone()
    
    if not current:
        return jsonify({'success': False, 'error': 'ไม่พบเอกสาร'})
    
    # Check if can edit
    doc_date = datetime.strptime(current[6][:10], '%Y-%m-%d').date()
    if doc_date < datetime.now().date():
        return jsonify({'success': False, 'error': 'ไม่สามารถแก้ไขเอกสารย้อนหลังได้'})
    
    # Reverse old stock
    c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
             (current[3], current[1]))
    
    # Update new stock
    c.execute('UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
             (data['quantity'], data['product_id']))
    
    # Update movement
    c.execute('UPDATE stock_movements SET product_id=?, quantity=?, reference=?, notes=? WHERE id=?',
             (data['product_id'], data['quantity'], data.get('reference', ''), data.get('notes', ''), movement_id))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/cancel_stock_in/<int:movement_id>', methods=['POST'])
def cancel_stock_in(movement_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get movement
    c.execute('SELECT * FROM stock_movements WHERE id = ?', (movement_id,))
    movement = c.fetchone()
    
    if not movement:
        return jsonify({'success': False, 'error': 'ไม่พบเอกสาร'})
    
    # Check if can cancel
    doc_date = datetime.strptime(movement[6][:10], '%Y-%m-%d').date()
    if doc_date < datetime.now().date():
        return jsonify({'success': False, 'error': 'ไม่สามารถยกเลิกเอกสารย้อนหลังได้'})
    
    # Reverse stock
    c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
             (movement[3], movement[1]))
    
    # Delete movement
    c.execute('DELETE FROM stock_movements WHERE id = ?', (movement_id,))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/process_stock_in', methods=['POST'])
def process_stock_in():
    data = request.get_json()
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Generate document number
    doc_no = generate_document_no(conn)
    
    # Update stock
    c.execute('UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
             (data['quantity'], data['product_id']))
    
    # Record movement
    c.execute('INSERT INTO stock_movements (product_id, type, quantity, reference, notes, document_no) VALUES (?, ?, ?, ?, ?, ?)',
             (data['product_id'], 'IN', data['quantity'], data.get('reference', ''), data.get('notes', ''), doc_no))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'document_no': doc_no})

@app.route('/stock_out')
@login_required
def stock_out():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode, current_stock FROM products WHERE current_stock > 0 ORDER BY name')
    products = c.fetchall()
    conn.close()
    return render_template('stock_out.html', products=products)

@app.route('/process_stock_out', methods=['POST'])
def process_stock_out():
    data = request.get_json()
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Check stock availability
    c.execute('SELECT current_stock FROM products WHERE id = ?', (data['product_id'],))
    current_stock = c.fetchone()[0]
    
    if current_stock < data['quantity']:
        return jsonify({'success': False, 'error': 'สต๊อกไม่เพียงพอ'})
    
    # Update stock
    c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
             (data['quantity'], data['product_id']))
    
    # Record movement
    c.execute('INSERT INTO stock_movements (product_id, type, quantity, reference, notes) VALUES (?, ?, ?, ?, ?)',
             (data['product_id'], 'OUT', data['quantity'], data.get('reference', ''), data.get('notes', '')))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/reports')
@login_required
def reports():
    return render_template('reports_menu.html')

@app.route('/movement_report')
@login_required
def movement_report():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Stock movements with product names
    c.execute('''SELECT sm.*, p.name, p.unit, p.barcode 
                FROM stock_movements sm 
                JOIN products p ON sm.product_id = p.id 
                ORDER BY p.barcode, sm.created_at DESC''')
    all_movements = c.fetchall()
    
    # Group movements by barcode
    movements_by_barcode = {}
    for movement in all_movements:
        barcode = movement[10] or 'ไม่มีบาร์โค้ด'
        if barcode not in movements_by_barcode:
            movements_by_barcode[barcode] = {
                'barcode': barcode,
                'product_name': movement[8],
                'movements': []
            }
        movements_by_barcode[barcode]['movements'].append(movement)
    
    # Low stock alerts
    c.execute('SELECT * FROM products WHERE current_stock <= min_stock')
    low_stock = c.fetchall()
    
    conn.close()
    return render_template('movement_report.html', movements_by_barcode=movements_by_barcode, low_stock=low_stock)

@app.route('/stock_summary_report')
@login_required
def stock_summary_report():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM products ORDER BY name')
    products = c.fetchall()
    
    conn.close()
    return render_template('stock_summary_report.html', products=products)

@app.route('/stock_out_list')
def stock_out_list():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('''SELECT sm.*, p.name, p.unit 
                FROM stock_movements sm 
                JOIN products p ON sm.product_id = p.id 
                WHERE sm.type = 'OUT'
                ORDER BY sm.created_at DESC''')
    stock_outs = c.fetchall()
    conn.close()
    return render_template('stock_out_list.html', stock_outs=stock_outs)

@app.route('/scan_barcode', methods=['POST'])
def scan_barcode():
    data = request.get_json()
    barcode = data.get('barcode')
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, current_stock FROM products WHERE barcode = ?', (barcode,))
    product = c.fetchone()
    conn.close()
    
    if product:
        return jsonify({'success': True, 'product': {'id': product[0], 'name': product[1], 'stock': product[2]}})
    else:
        return jsonify({'success': False, 'error': 'ไม่พบสินค้า'})

@app.route('/search_by_image', methods=['POST'])
def search_by_image():
    if 'image' not in request.files:
        return jsonify([])
    
    # Simple mock search - in real implementation, use image recognition
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode FROM products LIMIT 3')
    products = c.fetchall()
    conn.close()
    
    # Mock similarity scores
    results = []
    for i, product in enumerate(products):
        results.append({
            'id': product[0],
            'name': product[1],
            'barcode': product[2],
            'similarity': 95 - (i * 10)  # Mock similarity score
        })
    
    return jsonify(results)

@app.route('/export_movement_excel')
@login_required
def export_movement_excel():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    c.execute('''SELECT sm.*, p.name, p.unit, p.barcode 
                FROM stock_movements sm 
                JOIN products p ON sm.product_id = p.id 
                ORDER BY p.barcode, sm.created_at DESC''')
    movements = c.fetchall()
    conn.close()
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Movement data sheet
    worksheet = workbook.add_worksheet('Movement Report')
    headers = ['วันที่', 'เลขที่เอกสาร', 'บาร์โค้ด', 'ชื่อสินค้า', 'ประเภท', 'จำนวน', 'หน่วย', 'อ้างอิง', 'หมายเหตุ']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    for row, movement in enumerate(movements, 1):
        worksheet.write(row, 0, movement[6][:19])
        worksheet.write(row, 1, movement[7] or '')
        worksheet.write(row, 2, movement[10] or '')
        worksheet.write(row, 3, movement[8])
        worksheet.write(row, 4, 'รับเข้า' if movement[2] == 'IN' else 'เบิกออก')
        worksheet.write(row, 5, movement[3])
        worksheet.write(row, 6, movement[9])
        worksheet.write(row, 7, movement[4] or '')
        worksheet.write(row, 8, movement[5] or '')
    
    # Chart data sheet
    chart_sheet = workbook.add_worksheet('Chart Data')
    chart_sheet.write(0, 0, 'วันที่')
    chart_sheet.write(0, 1, 'รับเข้า')
    chart_sheet.write(0, 2, 'เบิกออก')
    
    # Calculate daily totals
    daily_data = {}
    for movement in movements:
        date = movement[6][:10]
        if date not in daily_data:
            daily_data[date] = {'in': 0, 'out': 0}
        if movement[2] == 'IN':
            daily_data[date]['in'] += movement[3]
        else:
            daily_data[date]['out'] += movement[3]
    
    # Write chart data
    for row, (date, data) in enumerate(sorted(daily_data.items()), 1):
        chart_sheet.write(row, 0, date)
        chart_sheet.write(row, 1, data['in'])
        chart_sheet.write(row, 2, data['out'])
    
    # Create chart
    chart = workbook.add_chart({'type': 'line'})
    chart.add_series({
        'name': 'รับเข้า',
        'categories': ['Chart Data', 1, 0, len(daily_data), 0],
        'values': ['Chart Data', 1, 1, len(daily_data), 1],
        'line': {'color': '#28a745'}
    })
    chart.add_series({
        'name': 'เบิกออก',
        'categories': ['Chart Data', 1, 0, len(daily_data), 0],
        'values': ['Chart Data', 1, 2, len(daily_data), 2],
        'line': {'color': '#dc3545'}
    })
    chart.set_title({'name': 'แนวโน้มการเคลื่อนไหวสต๊อก'})
    chart.set_x_axis({'name': 'วันที่'})
    chart.set_y_axis({'name': 'จำนวน'})
    
    # Insert chart into first sheet
    worksheet.insert_chart('K2', chart)
    
    workbook.close()
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=movement_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'}
    )

@app.route('/users')
@login_required
def users():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = c.fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        conn = sqlite3.connect('supply_inventory.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                     (username, password, role))
            conn.commit()
            return redirect(url_for('users'))
        except sqlite3.IntegrityError:
            return render_template('add_user.html', error='ชื่อผู้ใช้นี้มีอยู่แล้ว')
        finally:
            conn.close()
    return render_template('add_user.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('users'))

@app.route('/test_form', methods=['GET', 'POST'])
def test_form():
    if request.method == 'POST':
        test_name = request.form.get('test_name')
        print(f"Test form received: {test_name}")
        return f"Received: {test_name}"
    return render_template('test_form.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)