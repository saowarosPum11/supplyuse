from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3
import os
import base64

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
def index():
    return render_template('index.html')

@app.route('/products')
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
def reports():
    return render_template('reports_menu.html')

@app.route('/movement_report')
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

@app.route('/test_form', methods=['GET', 'POST'])
def test_form():
    if request.method == 'POST':
        test_name = request.form.get('test_name')
        print(f"Test form received: {test_name}")
        return f"Received: {test_name}"
    return render_template('test_form.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)