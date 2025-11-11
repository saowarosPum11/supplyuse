from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>ระบบเอกสาร</h1>
    <a href="/documents">ดูรายการเอกสาร</a><br>
    <a href="/document/new/RECEIVE">สร้างเอกสารรับเข้า</a>
    '''

@app.route('/documents')
def documents():
    return render_template('documents.html', documents=[])

@app.route('/document/new/<doc_type>')
def new_document(doc_type):
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, barcode, current_stock FROM products ORDER BY name')
    products = c.fetchall()
    conn.close()
    
    doc_no = f"{doc_type[:2]}2412001"
    return render_template('document_form.html', doc_type=doc_type, doc_no=doc_no, products=products)

@app.route('/document/save', methods=['POST'])
def save_document():
    try:
        data = request.get_json()
        
        # Simple validation
        if not data or not data.get('items'):
            return jsonify({'success': False, 'error': 'ไม่มีข้อมูล'})
        
        # Just return success for now
        return jsonify({'success': True, 'document_id': 1, 'message': 'บันทึกสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)