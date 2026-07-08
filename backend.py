from flask import Flask, render_template, request, redirect, url_for
from config import Config
import database

app = Flask(__name__)
app.config.from_object(Config)

CURRENT_USER_ID = 1

@app.route('/')
def catalog():
    conn = database.get_db_connection()
    artists = conn.execute('SELECT * FROM artists').fetchall()
    works = conn.execute('''
        SELECT p.*, a.username FROM portfolio_works p 
        JOIN artists a ON p.artist_id = a.id
    ''').fetchall()
    conn.close()
    return render_template('catalog.html', artists=artists, works=works)

@app.route('/artist/<int:artist_id>')
def artist_profile(artist_id):
    conn = database.get_db_connection()
    artist = conn.execute('SELECT * FROM artists WHERE id = ?', (artist_id,)).fetchone()
    if not artist:
        conn.close()
        return "Художник не найден", 404
        
    services = conn.execute('SELECT * FROM services WHERE artist_id = ?', (artist_id,)).fetchall()
    works = conn.execute('SELECT * FROM portfolio_works WHERE artist_id = ?', (artist_id,)).fetchall()
    
    compiled_services = []
    for service in services:
        variants = conn.execute('SELECT * FROM service_variants WHERE service_id = ?', (service['id'],)).fetchall()
        options = conn.execute('SELECT * FROM options WHERE service_id = ?', (service['id'],)).fetchall()
        compiled_services.append({
            'id': service['id'],
            'title': service['title'],
            'variants': variants,
            'options': options
        })
        
    conn.close()
    return render_template('profile.html', artist=artist, services=compiled_services, works=works)

@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        title = request.form.get('title')
        
        variant_titles = request.form.getlist('variant_title[]')
        variant_prices = request.form.getlist('variant_price[]')
        
        option_titles = request.form.getlist('option_title[]')
        option_prices = request.form.getlist('option_price[]')

        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO services (artist_id, title) VALUES (?, ?)', (CURRENT_USER_ID, title))
        service_id = cursor.lastrowid
        
        for v_title, v_price in zip(variant_titles, variant_prices):
            if v_title.strip() and v_price:
                cursor.execute('INSERT INTO service_variants (service_id, variant_title, price) VALUES (?, ?, ?)',
                               (service_id, v_title, float(v_price)))
                
        for o_title, o_price in zip(option_titles, option_prices):
            if o_title.strip() and o_price:
                cursor.execute('INSERT INTO options (service_id, option_title, additional_price) VALUES (?, ?, ?)',
                               (service_id, o_title, float(o_price)))
                
        conn.commit()
        conn.close()
        return redirect(url_for('artist_profile', artist_id=CURRENT_USER_ID))
        
    return render_template('add_service.html')

@app.route('/order', methods=['POST'])
def place_order():
    service_id = request.form.get('service_id')
    selected_variant = request.form.get('variant_id')
    selected_options = request.form.getlist('options')
    return f"<h3>Заказ принят!</h3>Услуга ID: {service_id}<br>Выбран вариант цены ID: {selected_variant}<br>Доп. опции ID: {selected_options}<br><a href='/'>В каталог</a>"

if __name__ == '__main__':
    database.init_db()
    app.run(debug=app.config['DEBUG'])