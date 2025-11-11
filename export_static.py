import os
from flask import Flask
from app import app, init_db
import sqlite3

def export_static_pages():
    """Export Flask app to static HTML files"""
    init_db()
    
    # Create static export directory
    os.makedirs('static_export', exist_ok=True)
    
    with app.test_client() as client:
        # Export login page
        response = client.get('/login')
        with open('static_export/index.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        # Login first
        client.post('/login', data={'username': '63010468', 'password': '63010468'})
        
        # Export main pages
        pages = {
            '/': 'home.html',
            '/products': 'products.html',
            '/stock_in': 'stock_in.html',
            '/stock_out': 'stock_out.html',
            '/reports': 'reports.html'
        }
        
        for route, filename in pages.items():
            try:
                response = client.get(route)
                if response.status_code == 200:
                    with open(f'static_export/{filename}', 'w', encoding='utf-8') as f:
                        f.write(response.get_data(as_text=True))
                    print(f'Exported: {filename}')
            except Exception as e:
                print(f'Error exporting {route}: {e}')

if __name__ == '__main__':
    export_static_pages()
    print('Static export completed!')