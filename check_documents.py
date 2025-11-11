import sqlite3

conn = sqlite3.connect('supply_inventory.db')
c = conn.cursor()

print("=== ตรวจสอบตาราง simple_documents ===")
try:
    c.execute('SELECT * FROM simple_documents')
    docs = c.fetchall()
    print(f"จำนวนเอกสาร: {len(docs)}")
    for doc in docs:
        print(f"ID: {doc[0]}, เลขที่: {doc[1]}, ประเภท: {doc[2]}, วันที่: {doc[3]}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== ตรวจสอบตาราง simple_document_items ===")
try:
    c.execute('SELECT * FROM simple_document_items')
    items = c.fetchall()
    print(f"จำนวนรายการ: {len(items)}")
    for item in items:
        print(f"Doc ID: {item[1]}, Product ID: {item[2]}, จำนวน: {item[3]}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== ตรวจสอบ Query ที่ใช้ในหน้ารายการ ===")
try:
    c.execute('''SELECT d.*, COUNT(di.id) as item_count
                FROM simple_documents d 
                LEFT JOIN simple_document_items di ON d.id = di.document_id
                GROUP BY d.id
                ORDER BY d.created_at DESC''')
    result = c.fetchall()
    print(f"ผลลัพธ์ Query: {len(result)} รายการ")
    for row in result:
        print(f"เอกสาร: {row[1]}, ประเภท: {row[2]}, รายการ: {row[8]}")
except Exception as e:
    print(f"Error: {e}")

conn.close()