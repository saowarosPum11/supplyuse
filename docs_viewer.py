from flask import Flask, render_template_string
import markdown
import os

app = Flask(__name__)

@app.route('/')
def docs_menu():
    return '''
    <h1>📚 เอกสารระบบจัดการสต๊อก</h1>
    <ul>
        <li><a href="/user-manual">คู่มือการใช้งาน</a></li>
        <li><a href="/documentation">เอกสารเทคนิค</a></li>
        <li><a href="/api-reference">API Reference</a></li>
    </ul>
    <p><a href="http://localhost:5000">← กลับไประบบหลัก</a></p>
    '''

@app.route('/user-manual')
def user_manual():
    with open('USER_MANUAL.md', 'r', encoding='utf-8') as f:
        content = f.read()
    html = markdown.markdown(content)
    return f'<div style="max-width:800px;margin:auto;padding:20px">{html}</div>'

@app.route('/documentation')
def documentation():
    with open('DOCUMENTATION.md', 'r', encoding='utf-8') as f:
        content = f.read()
    html = markdown.markdown(content)
    return f'<div style="max-width:800px;margin:auto;padding:20px">{html}</div>'

@app.route('/api-reference')
def api_reference():
    with open('API_REFERENCE.md', 'r', encoding='utf-8') as f:
        content = f.read()
    html = markdown.markdown(content)
    return f'<div style="max-width:800px;margin:auto;padding:20px">{html}</div>'

if __name__ == '__main__':
    # app.run(port=5001, debug=True)
    pass