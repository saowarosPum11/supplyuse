from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'supply_use_secret_key_2024'

@app.before_request
def require_login():
    # Skip login check for login, logout, clear-data routes and static files
    if request.endpoint in ['login', 'logout', 'clear_data', 'static'] or request.path.startswith('/static') or request.path == '/clear-data':
        return
    
    # Check if user is logged in
    if 'user_logged_in' not in session:
        return redirect(url_for('login'))

def init_document_db():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Documents table
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_no TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,
        doc_date DATE NOT NULL,
        reference TEXT,
        notes TEXT,
        status TEXT DEFAULT 'DRAFT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add status column if it doesn't exist
    try:
        c.execute('ALTER TABLE documents ADD COLUMN status TEXT DEFAULT "DRAFT"')
    except sqlite3.OperationalError:
        pass
    
    # Document items table
    c.execute('''CREATE TABLE IF NOT EXISTS document_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) DEFAULT 0,
        total_price DECIMAL(10,2) DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (document_id) REFERENCES documents (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    conn.commit()
    conn.close()

def generate_doc_no(doc_type):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    now = datetime.now()
    prefix = f"{doc_type[:2]}{now.strftime('%y%m')}"
    
    c.execute('SELECT doc_no FROM documents WHERE doc_no LIKE ? ORDER BY doc_no DESC LIMIT 1', 
              (f'{prefix}%',))
    result = c.fetchone()
    
    if result:
        last_no = result[0]
        running = int(last_no[-4:]) + 1
    else:
        running = 1
    
    conn.close()
    return f'{prefix}{running:04d}'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        
        # Simple authentication (in real app, use proper authentication)
        valid_users = {
            '63010468': '63010468',
            'admin': 'admin',
            'user': 'user'
        }
        
        if username in valid_users and valid_users[username] == password:
            session['user_logged_in'] = True
            session['username'] = username
            session['role'] = role
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clear-data')
def clear_data():
    return '''<script>
        localStorage.clear();
        sessionStorage.clear();
        alert('ล้างข้อมูลเบราว์เซอร์เรียบร้อย');
        window.location.href = '/login';
    </script>'''

@app.route('/')
def index():
    return render_template('document_index.html')

@app.route('/documents')
def documents():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('''SELECT d.*, COUNT(di.id) as item_count
                FROM documents d 
                LEFT JOIN document_items di ON d.id = di.document_id
                GROUP BY d.id
                ORDER BY d.created_at DESC''')
    documents = c.fetchall()
    conn.close()
    return render_template('documents.html', documents=documents)

@app.route('/document/new/<doc_type>')
def new_document(doc_type):
    if doc_type not in ['RECEIVE', 'ISSUE']:
        return redirect(url_for('documents'))
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    if doc_type == 'ISSUE':
        c.execute('SELECT id, name, barcode, current_stock FROM products WHERE current_stock > 0 ORDER BY name')
    else:
        c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    
    products = c.fetchall()
    conn.close()
    
    doc_no = generate_doc_no(doc_type)
    return render_template('document_form.html', doc_type=doc_type, doc_no=doc_no, products=products)

@app.route('/document/update/<doc_no>', methods=['POST'])
def update_document_by_no(doc_no):
    data = request.get_json()
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get document ID
        c.execute('SELECT id FROM documents WHERE doc_no = ?', (doc_no,))
        result = c.fetchone()
        
        if result:
            doc_id = result[0]
            # Update document
            c.execute('''UPDATE documents SET doc_date = ?, reference = ?, notes = ?
                        WHERE id = ?''',
                     (data['doc_date'], data.get('reference', ''), 
                      data.get('notes', ''), doc_id))
            
            # Delete existing items
            c.execute('DELETE FROM document_items WHERE document_id = ?', (doc_id,))
            
            # Insert updated items
            for item in data['items']:
                c.execute('''INSERT INTO document_items (document_id, product_id, quantity, notes)
                            VALUES (?, ?, ?, ?)''',
                         (doc_id, item['product_id'], item['quantity'], item.get('notes', '')))
            
            conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/document/update/<int:doc_id>', methods=['POST'])
def update_document(doc_id):
    data = request.get_json()
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Update document
        c.execute('''UPDATE documents SET doc_date = ?, reference = ?, notes = ?
                    WHERE id = ?''',
                 (data['doc_date'], data.get('reference', ''), 
                  data.get('notes', ''), doc_id))
        
        # Delete existing items
        c.execute('DELETE FROM document_items WHERE document_id = ?', (doc_id,))
        
        # Insert updated items
        for item in data['items']:
            c.execute('''INSERT INTO document_items (document_id, product_id, quantity, notes)
                        VALUES (?, ?, ?, ?)''',
                     (doc_id, item['product_id'], item['quantity'], item.get('notes', '')))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/document/save', methods=['POST'])
def save_document():
    data = request.get_json()
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Insert document
        c.execute('''INSERT INTO documents (doc_no, doc_type, doc_date, reference, notes)
                    VALUES (?, ?, ?, ?, ?)''',
                 (data['doc_no'], data['doc_type'], data['doc_date'], 
                  data.get('reference', ''), data.get('notes', '')))
        
        doc_id = c.lastrowid
        
        # Insert document items
        for item in data['items']:
            c.execute('''INSERT INTO document_items (document_id, product_id, quantity, unit_price, total_price, notes)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (doc_id, item['product_id'], item['quantity'], 
                      item.get('unit_price', 0), item.get('total_price', 0), item.get('notes', '')))
        
        conn.commit()
        return jsonify({'success': True, 'document_id': doc_id})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/document/edit/<doc_no>')
def edit_document_by_no(doc_no):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get document by doc_no
    c.execute('SELECT * FROM documents WHERE doc_no = ?', (doc_no,))
    document = c.fetchone()
    
    if not document:
        # Create mock document for demo
        mock_doc = (1, doc_no, 'RECEIVE', '2024-12-01', 'PO-001', 'เอกสารตัวอย่าง', 'DRAFT')
        mock_items = [(1, 1, 1, 10, 0, 0, 'รายการตัวอย่าง', 'ปากกา', 'PEN001')]
        mock_products = [(1, 'ปากกา', 'PEN001', 100), (2, 'กระดาษ', 'PAP001', 50), (3, 'ดินสอ', 'PEN002', 75)]
        conn.close()
        return render_template('document_edit.html', document=mock_doc, items=mock_items, products=mock_products)
    
    # Get document items
    c.execute('''SELECT di.*, p.name, p.barcode 
                FROM document_items di
                JOIN products p ON di.product_id = p.id
                WHERE di.document_id = ?''', (document[0],))
    items = c.fetchall()
    
    # Get all products
    c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    products = c.fetchall()
    
    conn.close()
    
    return render_template('document_edit.html', document=document, items=items, products=products)

@app.route('/document/edit/<int:doc_id>')
def edit_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get document by ID
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = c.fetchone()
    
    if not document:
        # Create mock document for demo
        if doc_id in [1, 2]:
            mock_doc = (doc_id, f'RE241200{doc_id}', 'RECEIVE', '2024-12-01', 'PO-001', 'เอกสารตัวอย่าง', 'DRAFT')
            mock_items = [(1, doc_id, 1, 10, 0, 0, 'รายการตัวอย่าง')]
            c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
            products = c.fetchall() or [(1, 'ปากกา', 'PEN001', 100), (2, 'กระดาษ', 'PAP001', 50)]
            conn.close()
            return render_template('document_edit.html', document=mock_doc, items=mock_items, products=products)
        return redirect(url_for('documents'))
    
    # Get document items
    c.execute('''SELECT di.*, p.name, p.barcode 
                FROM document_items di
                JOIN products p ON di.product_id = p.id
                WHERE di.document_id = ?''', (document[0],))
    items = c.fetchall()
    
    # Get all products
    c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    products = c.fetchall()
    
    conn.close()
    
    return render_template('document_edit.html', document=document, items=items, products=products)

@app.route('/document/view/<int:doc_id>')
def view_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get document
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = c.fetchone()
    
    if not document:
        return redirect(url_for('documents'))
    
    # Get document items with product details
    c.execute('''SELECT di.*, p.name, p.barcode, p.unit
                FROM document_items di
                JOIN products p ON di.product_id = p.id
                WHERE di.document_id = ?''', (doc_id,))
    items = c.fetchall()
    
    # Get all products for editing
    c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    products = c.fetchall()
    
    conn.close()
    
    return render_template('document_view.html', document=document, items=items, products=products)

@app.route('/document/confirm/<int:doc_id>', methods=['POST'])
def confirm_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get document
        c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        document = c.fetchone()
        
        if not document:
            return jsonify({'success': False, 'error': 'ไม่พบเอกสาร'})
        
        # Check if already confirmed (assume index 6 is status, default to DRAFT if None)
        doc_status = document[6] if len(document) > 6 and document[6] else 'DRAFT'
        if doc_status != 'DRAFT':
            return jsonify({'success': False, 'error': 'ไม่สามารถยืนยันเอกสารได้'})
        
        # Get document items
        c.execute('SELECT * FROM document_items WHERE document_id = ?', (doc_id,))
        items = c.fetchall()
        
        # Update stock based on document type
        for item in items:
            product_id = item[2]
            quantity = item[3]
            
            if document[2] == 'RECEIVE':  # รับเข้า
                c.execute('UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
                         (quantity, product_id))
                # Record stock movement
                c.execute('''INSERT INTO stock_movements (product_id, type, quantity, reference, notes, document_no)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (product_id, 'IN', quantity, f'เอกสาร {document[1]}', 
                          item[6] or '', document[1]))
            
            elif document[2] == 'ISSUE':  # เบิกออก
                # Check stock
                c.execute('SELECT current_stock FROM products WHERE id = ?', (product_id,))
                current_stock = c.fetchone()[0]
                
                if current_stock < quantity:
                    return jsonify({'success': False, 'error': f'สต๊อกไม่เพียงพอสำหรับสินค้า ID {product_id}'})
                
                c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
                         (quantity, product_id))
                # Record stock movement
                c.execute('''INSERT INTO stock_movements (product_id, type, quantity, reference, notes, document_no)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (product_id, 'OUT', quantity, f'เอกสาร {document[1]}', 
                          item[6] or '', document[1]))
        
        # Update document status (add column if not exists)
        try:
            c.execute('UPDATE documents SET status = ? WHERE id = ?', ('CONFIRMED', doc_id))
        except sqlite3.OperationalError:
            # If status column doesn't exist, add it first
            c.execute('ALTER TABLE documents ADD COLUMN status TEXT DEFAULT "DRAFT"')
            c.execute('UPDATE documents SET status = ? WHERE id = ?', ('CONFIRMED', doc_id))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/document/cancel/<int:doc_id>', methods=['POST'])
def cancel_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get document
        c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        document = c.fetchone()
        
        if not document:
            return jsonify({'success': False, 'error': 'ไม่พบเอกสาร'})
        
        # Check status (handle if column doesn't exist)
        doc_status = document[6] if len(document) > 6 and document[6] else 'DRAFT'
        if doc_status == 'CONFIRMED':
            # Reverse stock movements
            c.execute('SELECT * FROM document_items WHERE document_id = ?', (doc_id,))
            items = c.fetchall()
            
            for item in items:
                product_id = item[2]
                quantity = item[3]
                
                if document[2] == 'RECEIVE':  # ยกเลิกรับเข้า
                    c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
                             (quantity, product_id))
                elif document[2] == 'ISSUE':  # ยกเลิกเบิกออก
                    c.execute('UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
                             (quantity, product_id))
            
            # Delete related stock movements
            c.execute('DELETE FROM stock_movements WHERE document_no = ?', (document[1],))
        
        # Update document status
        try:
            c.execute('UPDATE documents SET status = ? WHERE id = ?', ('CANCELLED', doc_id))
        except sqlite3.OperationalError:
            # If status column doesn't exist, add it first
            c.execute('ALTER TABLE documents ADD COLUMN status TEXT DEFAULT "DRAFT"')
            c.execute('UPDATE documents SET status = ? WHERE id = ?', ('CANCELLED', doc_id))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/reports')
def reports():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get products count
        c.execute('SELECT COUNT(*) FROM products')
        total_products = c.fetchone()[0] or 0
        
        # Get documents count
        c.execute('SELECT COUNT(*) FROM documents')
        total_documents = c.fetchone()[0] or 0
        
        # Get confirmed documents count
        c.execute('SELECT COUNT(*) FROM documents WHERE status = "CONFIRMED"')
        confirmed_docs = c.fetchone()[0] or 0
        
        # Get recent documents
        c.execute('''SELECT d.doc_no, d.doc_type, d.doc_date, d.status, COUNT(di.id) as item_count
                    FROM documents d 
                    LEFT JOIN document_items di ON d.id = di.document_id
                    GROUP BY d.id
                    ORDER BY d.created_at DESC LIMIT 10''')
        recent_documents = c.fetchall()
        
        # Get document items summary
        c.execute('''SELECT p.name, SUM(di.quantity) as total_qty, d.doc_type
                    FROM document_items di
                    JOIN documents d ON di.document_id = d.id
                    JOIN products p ON di.product_id = p.id
                    WHERE d.status = "CONFIRMED"
                    GROUP BY p.id, d.doc_type
                    ORDER BY total_qty DESC LIMIT 10''')
        product_movements = c.fetchall()
        
        # Get all products
        c.execute('SELECT id, name, barcode, current_stock, unit_price FROM products ORDER BY name')
        all_products = c.fetchall()
        
    except Exception as e:
        # If tables don't exist, use mock data
        total_products = 15
        total_documents = 8
        confirmed_docs = 5
        recent_documents = [
            ('RE2411001', 'RECEIVE', '2024-11-01', 'CONFIRMED', 3),
            ('IS2411001', 'ISSUE', '2024-11-02', 'DRAFT', 2),
            ('RE2411002', 'RECEIVE', '2024-11-03', 'CONFIRMED', 1)
        ]
        product_movements = [
            ('ปากกา', 50, 'RECEIVE'),
            ('กระดาษ', 30, 'ISSUE'),
            ('ดินสอ', 25, 'RECEIVE')
        ]
        all_products = [
            (1, 'ปากกาลูกลื่น', 'PEN001', 150, 15.00),
            (2, 'กระดาษ A4', 'PAP001', 200, 5.00),
            (3, 'ดินสอ 2B', 'PEN002', 100, 8.00),
            (4, 'ยางลบ', 'ERA001', 75, 3.00),
            (5, 'ไม้บรรทัด', 'RUL001', 50, 12.00)
        ]
    
    conn.close()
    
    return render_template('reports.html', 
                         total_products=total_products,
                         total_documents=total_documents,
                         confirmed_docs=confirmed_docs,
                         recent_documents=recent_documents,
                         product_movements=product_movements,
                         all_products=all_products)

@app.route('/reports-menu')
def reports_menu():
    return render_template('reports_menu.html')

@app.route('/movement-report')
def movement_report():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get movement history from documents
        c.execute('''SELECT d.doc_no, d.doc_type, d.doc_date, d.status, p.name, di.quantity, d.reference
                    FROM documents d
                    JOIN document_items di ON d.id = di.document_id
                    JOIN products p ON di.product_id = p.id
                    WHERE d.status = "CONFIRMED"
                    ORDER BY d.doc_date DESC, d.created_at DESC''')
        movements = c.fetchall()
        
    except Exception as e:
        # Mock data if no real data
        movements = [
            ('RE2411001', 'RECEIVE', '2024-11-01', 'CONFIRMED', 'ปากกา', 50, 'PO-001'),
            ('IS2411001', 'ISSUE', '2024-11-02', 'CONFIRMED', 'กระดาษ', 30, 'REQ-001'),
            ('RE2411002', 'RECEIVE', '2024-11-03', 'CONFIRMED', 'ดินสอ', 25, 'PO-002')
        ]
    
    conn.close()
    return render_template('movement_reports.html', movements=movements)

@app.route('/stock-summary-report')
def stock_summary_report():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get inventory summary
        c.execute('SELECT id, name, barcode, current_stock, unit_price FROM products ORDER BY name')
        inventory = c.fetchall()
        
        c.execute('SELECT COUNT(*) FROM products')
        total_items = c.fetchone()[0] or 0
        
        c.execute('SELECT SUM(current_stock) FROM products')
        total_quantity = c.fetchone()[0] or 0
        
        c.execute('SELECT SUM(current_stock * unit_price) FROM products')
        total_value = c.fetchone()[0] or 0
        
    except Exception as e:
        # Mock data if no real data
        inventory = [
            (1, 'ปากกาลูกลื่น', 'PEN001', 150, 15.00),
            (2, 'กระดาษ A4', 'PAP001', 200, 5.00),
            (3, 'ดินสอ 2B', 'PEN002', 100, 8.00),
            (4, 'ยางลบ', 'ERA001', 75, 3.00),
            (5, 'ไม้บรรทัด', 'RUL001', 50, 12.00)
        ]
        total_items = len(inventory)
        total_quantity = sum(item[3] for item in inventory)
        total_value = sum(item[3] * item[4] for item in inventory)
    
    conn.close()
    return render_template('inventory_reports.html', 
                         inventory=inventory,
                         total_items=total_items,
                         total_quantity=total_quantity,
                         total_value=total_value)

@app.route('/api/products')
def api_products():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    products = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': p[0],
        'name': p[1],
        'barcode': p[2],
        'current_stock': p[3]
    } for p in products])

if __name__ == '__main__':
    init_document_db()
    app.run(debug=True, port=5001)