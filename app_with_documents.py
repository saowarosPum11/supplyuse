from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3
from document_manager import document_bp, init_document_db

app = Flask(__name__)

# Initialize document database
init_document_db()

# Register document blueprint
app.register_blueprint(document_bp)

# Add basic route
@app.route('/')
def index():
    return '<h1>ระบบจัดการเอกสาร</h1><a href="/documents">ไปที่หน้าเอกสาร</a>'

if __name__ == '__main__':
    app.run(debug=True, port=5001)