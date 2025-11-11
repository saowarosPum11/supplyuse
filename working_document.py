from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Drop old tables
    c.execute('DROP TABLE IF EXISTS working_documents')
    c.execute('DROP TABLE IF EXISTS working_document_items')
    
    # Create new tables
    c.execute('''CREATE TABLE working_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_no TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,
        doc_date DATE NOT NULL,
        reference TEXT,
        notes TEXT,
        confirmed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE working_document_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (document_id) REFERENCES working_documents (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('simple_document_index.html')

@app.route('/documents')
def documents():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('''SELECT d.*, COUNT(di.id) as item_count
                FROM working_documents d 
                LEFT JOIN working_document_items di ON d.id = di.document_id
                GROUP BY d.id
                ORDER BY d.created_at DESC''')
    documents = c.fetchall()
    conn.close()
    return render_template('documents.html', documents=documents)

@app.route('/document/new/<doc_type>')
def new_document(doc_type):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    products = c.fetchall()
    conn.close()
    
    now = datetime.now()
    doc_no = f"{doc_type[:2]}{now.strftime('%y%m')}001"
    
    return render_template('document_form.html', doc_type=doc_type, doc_no=doc_no, products=products)

@app.route('/document/save', methods=['POST'])
def save_document():
    data = request.get_json()
    
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    try:
        # Insert document
        c.execute('''INSERT INTO working_documents (doc_no, doc_type, doc_date, reference, notes)
                    VALUES (?, ?, ?, ?, ?)''',
                 (data['doc_no'], data['doc_type'], data['doc_date'], 
                  data.get('reference', ''), data.get('notes', '')))
        
        doc_id = c.lastrowid
        
        # Insert items
        for item in data['items']:
            c.execute('''INSERT INTO working_document_items (document_id, product_id, quantity, unit_price, notes)
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
    
    c.execute('SELECT * FROM working_documents WHERE id = ?', (doc_id,))
    document = c.fetchone()
    
    c.execute('''SELECT di.*, p.name, p.barcode, p.unit
                FROM working_document_items di
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
        c.execute('SELECT * FROM working_documents WHERE id = ?', (doc_id,))
        document = c.fetchone()
        
        c.execute('SELECT * FROM working_document_items WHERE document_id = ?', (doc_id,))
        items = c.fetchall()
        
        for item in items:
            product_id = item[2]
            quantity = item[3]
            
            if document[2] == 'RECEIVE':
                c.execute('UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
                         (quantity, product_id))
            elif document[2] == 'ISSUE':
                c.execute('UPDATE products SET current_stock = current_stock - ? WHERE id = ?',
                         (quantity, product_id))
        
        c.execute('UPDATE working_documents SET confirmed = 1 WHERE id = ?', (doc_id,))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)