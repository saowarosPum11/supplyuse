from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3

app = Flask(__name__)

def init_simple_db():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Simple documents table without status
    c.execute('''CREATE TABLE IF NOT EXISTS simple_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_no TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,
        doc_date DATE NOT NULL,
        reference TEXT,
        notes TEXT,
        confirmed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Document items table
    c.execute('''CREATE TABLE IF NOT EXISTS simple_document_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (document_id) REFERENCES simple_documents (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    conn.commit()
    conn.close()

def generate_simple_doc_no(doc_type):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    now = datetime.now()
    prefix = f"{doc_type[:2]}{now.strftime('%y%m')}"
    
    c.execute('SELECT doc_no FROM simple_documents WHERE doc_no LIKE ? ORDER BY doc_no DESC LIMIT 1', 
              (f'{prefix}%',))
    result = c.fetchone()
    
    if result:
        last_no = result[0]
        running = int(last_no[-4:]) + 1
    else:
        running = 1
    
    conn.close()
    return f'{prefix}{running:04d}'

@app.route('/')
def index():
    return render_template('simple_document_index.html')

@app.route('/documents')
def documents():
    # Try to get real data first
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    try:
        c.execute('''SELECT d.*, COUNT(di.id) as item_count
                    FROM simple_documents d 
                    LEFT JOIN simple_document_items di ON d.id = di.document_id
                    GROUP BY d.id
                    ORDER BY d.created_at DESC''')
        documents = c.fetchall()
    except:
        documents = []
    
    print(f"Found {len(documents)} documents in database")
    
    # If no data, show empty with sample data in template
    
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
    
    doc_no = generate_simple_doc_no(doc_type)
    return render_template('document_form.html', doc_type=doc_type, doc_no=doc_no, products=products)

@app.route('/document/save', methods=['POST'])
def save_document():
    data = request.get_json()
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Insert document
        c.execute('''INSERT INTO simple_documents (doc_no, doc_type, doc_date, reference, notes)
                    VALUES (?, ?, ?, ?, ?)''',
                 (data['doc_no'], data['doc_type'], data['doc_date'], 
                  data.get('reference', ''), data.get('notes', '')))
        
        doc_id = c.lastrowid
        
        # Insert document items
        for item in data['items']:
            c.execute('''INSERT INTO simple_document_items (document_id, product_id, quantity, unit_price, notes)
                        VALUES (?, ?, ?, ?, ?)''',
                     (doc_id, item['product_id'], item['quantity'], 
                      item.get('unit_price', 0), item.get('notes', '')))
        
        conn.commit()
        return jsonify({'success': True, 'document_id': doc_id})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/document/view/<int:doc_id>')
def view_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Get document
    c.execute('SELECT * FROM simple_documents WHERE id = ?', (doc_id,))
    document = c.fetchone()
    
    if not document:
        return redirect(url_for('documents'))
    
    # Get document items with product details
    c.execute('''SELECT di.*, p.name, p.barcode, p.unit
                FROM simple_document_items di
                JOIN products p ON di.product_id = p.id
                WHERE di.document_id = ?''', (doc_id,))
    items = c.fetchall()
    
    conn.close()
    
    return render_template('simple_document_view.html', document=document, items=items)

@app.route('/document/confirm/<int:doc_id>', methods=['POST'])
def confirm_document(doc_id):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Get document
        c.execute('SELECT * FROM simple_documents WHERE id = ?', (doc_id,))
        document = c.fetchone()
        
        if not document or document[6] == 1:  # already confirmed
            return jsonify({'success': False, 'error': 'ไม่สามารถยืนยันเอกสารได้'})
        
        # Get document items
        c.execute('SELECT * FROM simple_document_items WHERE document_id = ?', (doc_id,))
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
        
        # Update document confirmed status
        c.execute('UPDATE simple_documents SET confirmed = 1 WHERE id = ?', (doc_id,))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    init_simple_db()
    app.run(debug=True, port=5001)