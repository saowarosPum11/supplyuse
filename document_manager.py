from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3

document_bp = Blueprint('document', __name__)

def init_document_db():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Documents table
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_no TEXT UNIQUE NOT NULL,
        doc_type TEXT CHECK(doc_type IN ('RECEIVE', 'ISSUE')),
        doc_date DATE,
        reference TEXT,
        notes TEXT,
        status TEXT DEFAULT 'DRAFT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Document items table
    c.execute('''CREATE TABLE IF NOT EXISTS document_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price DECIMAL(10,2) DEFAULT 0,
        FOREIGN KEY (document_id) REFERENCES documents (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    conn.commit()
    conn.close()

def generate_doc_no(doc_type):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    prefix = 'RCV' if doc_type == 'RECEIVE' else 'ISS'
    today = datetime.now().strftime('%y%m%d')
    
    c.execute('SELECT doc_no FROM documents WHERE doc_no LIKE ? ORDER BY doc_no DESC LIMIT 1', 
              (f'{prefix}{today}%',))
    result = c.fetchone()
    
    if result:
        last_no = int(result[0][-3:])
        new_no = last_no + 1
    else:
        new_no = 1
    
    conn.close()
    return f'{prefix}{today}{new_no:03d}'

@document_bp.route('/documents')
def document_list():
    init_document_db()
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT * FROM documents ORDER BY created_at DESC')
    documents = c.fetchall()
    conn.close()
    return render_template('documents.html', documents=documents)

@document_bp.route('/document/new/<doc_type>')
def new_document(doc_type):
    init_document_db()
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode, unit FROM products ORDER BY name')
    products = c.fetchall()
    conn.close()
    
    doc_no = generate_doc_no(doc_type)
    return render_template('document_form.html', 
                         doc_type=doc_type, 
                         doc_no=doc_no, 
                         products=products)

@document_bp.route('/document/save', methods=['POST'])
def save_document():
    data = request.get_json()
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Save document header
        c.execute('''INSERT INTO documents (doc_no, doc_type, doc_date, reference, notes, status)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (data['doc_no'], data['doc_type'], data['doc_date'], 
                  data['reference'], data['notes'], data['status']))
        
        doc_id = c.lastrowid
        
        # Save document items
        for item in data['items']:
            c.execute('''INSERT INTO document_items (document_id, product_id, quantity, unit_price)
                        VALUES (?, ?, ?, ?)''',
                     (doc_id, item['product_id'], item['quantity'], item.get('unit_price', 0)))
        
        # Update stock if confirmed
        if data['status'] == 'CONFIRMED':
            for item in data['items']:
                if data['doc_type'] == 'RECEIVE':
                    c.execute('UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
                             (item['quantity'], item['product_id']))
                else:  # ISSUE
                    c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
                             (item['quantity'], item['product_id']))
        
        conn.commit()
        return jsonify({'success': True, 'doc_id': doc_id})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@document_bp.route('/document/view/<int:doc_id>')
def view_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get document header
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    document = c.fetchone()
    
    # Get document items
    c.execute('''SELECT di.*, p.name, p.unit 
                FROM document_items di
                JOIN products p ON di.product_id = p.id
                WHERE di.document_id = ?''', (doc_id,))
    items = c.fetchall()
    
    conn.close()
    return render_template('document_view.html', document=document, items=items)