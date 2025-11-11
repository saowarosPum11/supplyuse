from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>ระบบเอกสาร</h1>
    <a href="/documents">ดูรายการเอกสาร</a><br>
    <a href="/create_test_data">สร้างข้อมูลทดสอบ</a>
    '''

@app.route('/create_test_data')
def create_test_data():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    
    # Create tables
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
    
    # Insert test data
    test_docs = [
        ('RE001', 'RECEIVE', '2024-12-01', 'PO-001', 'รับเข้าสินค้า', 0),
        ('IS001', 'ISSUE', '2024-12-02', 'REQ-001', 'เบิกสินค้า', 1),
        ('RE002', 'RECEIVE', '2024-12-03', 'PO-002', 'รับเข้าเพิ่ม', 0)
    ]
    
    for doc in test_docs:
        try:
            c.execute('INSERT INTO simple_documents (doc_no, doc_type, doc_date, reference, notes, confirmed) VALUES (?, ?, ?, ?, ?, ?)', doc)
        except:
            pass
    
    conn.commit()
    conn.close()
    return 'สร้างข้อมูลเรียบร้อย <a href="/documents">ดูรายการ</a>'

@app.route('/documents')
def documents():
    conn = sqlite3.connect('supply_inventory.db')
    c = conn.cursor()
    c.execute('SELECT * FROM simple_documents ORDER BY created_at DESC')
    docs = c.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>รายการเอกสาร</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h2>รายการเอกสาร</h2>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>เลขที่เอกสาร</th>
                        <th>ประเภท</th>
                        <th>วันที่</th>
                        <th>อ้างอิง</th>
                        <th>สถานะ</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    if docs:
        for doc in docs:
            status = 'ยืนยันแล้ว' if doc[6] == 1 else 'ร่าง'
            doc_type = 'รับเข้า' if doc[2] == 'RECEIVE' else 'เบิกออก'
            html += f'''
                    <tr>
                        <td>{doc[1]}</td>
                        <td><span class="badge bg-{'success' if doc[2] == 'RECEIVE' else 'warning'}">{doc_type}</span></td>
                        <td>{doc[3]}</td>
                        <td>{doc[4] or '-'}</td>
                        <td><span class="badge bg-{'primary' if doc[6] == 1 else 'secondary'}">{status}</span></td>
                    </tr>
            '''
    else:
        html += '<tr><td colspan="5" class="text-center">ไม่มีข้อมูล</td></tr>'
    
    html += '''
                </tbody>
            </table>
            <p>จำนวนเอกสารทั้งหมด: ''' + str(len(docs)) + '''</p>
            <a href="/" class="btn btn-secondary">กลับหน้าหลัก</a>
        </div>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    app.run(debug=True, port=5002)