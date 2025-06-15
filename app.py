from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = 'tarixiy_obidalar_secret_key'

# Ma'lumotlar bazasi bilan ishlash funksiyasi
def get_db_connection():
    conn = sqlite3.connect('obidalar.db')
    conn.row_factory = sqlite3.Row
    return conn

# Login kerak bo'lgan sahifalar uchun dekorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Iltimos, avval tizimga kiring', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Super admin kerak bo'lgan sahifalar uchun dekorator
def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_superadmin'):
            flash('Bu sahifaga faqat super admin kirishi mumkin', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Asosiy sahifa
@app.route('/')
def index():
    conn = get_db_connection()
    obidalar = conn.execute('SELECT * FROM obidalar').fetchall()
    
    # Restavratsiyalangan va kutilayotgan obidalar guruhlari
    restavratsiyalangan = [obida for obida in obidalar if obida['guruh'] == 'Restavratsiyalangan']
    kutilayotgan = [obida for obida in obidalar if obida['guruh'] == 'Restavratsiya kutilayotgan']
    
    # O'qilmagan xabarlar sonini olish (adminlar uchun bildirish)
    if 'user_id' in session:
        yangi_xabarlar = conn.execute('SELECT COUNT(*) FROM xabarlar WHERE oqilgan = 0').fetchone()[0]
        session['yangi_xabarlar'] = yangi_xabarlar
    
    conn.close()
    return render_template('index.html', 
                           restavratsiyalangan=restavratsiyalangan, 
                           kutilayotgan=kutilayotgan)

# Paxsa turidagi obidalar
@app.route('/paxsa')
def paxsa():
    conn = get_db_connection()
    obidalar = conn.execute('SELECT * FROM obidalar WHERE turi = "Paxsa"').fetchall()
    conn.close()
    return render_template('obida_turi.html', obidalar=obidalar, tur="Paxsa")

# Gil turidagi obidalar
@app.route('/gil')
def gil():
    conn = get_db_connection()
    obidalar = conn.execute('SELECT * FROM obidalar WHERE turi = "Gil"').fetchall()
    conn.close()
    return render_template('obida_turi.html', obidalar=obidalar, tur="Gil")

# Obida batafsilini ko'rish
@app.route('/obida/<int:id>')
def obida_view(id):
    conn = get_db_connection()
    obida = conn.execute('SELECT * FROM obidalar WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if obida is None:
        flash('Obida topilmadi', 'danger')
        return redirect(url_for('index'))
    
    return render_template('obida_view.html', obida=obida)

# Qidiruv funksiyasi
@app.route('/qidiruv')
def qidiruv():
    qidiruv_soz = request.args.get('q', '')
    
    if not qidiruv_soz:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    obidalar = conn.execute(
        'SELECT * FROM obidalar WHERE nomi LIKE ? OR manzili LIKE ?', 
        (f'%{qidiruv_soz}%', f'%{qidiruv_soz}%')
    ).fetchall()
    conn.close()
    
    return render_template('qidiruv.html', obidalar=obidalar, qidiruv_soz=qidiruv_soz)

# Filtrlash funksiyasi
@app.route('/filtr')
def filtr():
    guruh = request.args.get('guruh', '')
    yil = request.args.get('yil', '')
    tur = request.args.get('tur', '')
    
    query = 'SELECT * FROM obidalar WHERE 1=1'
    params = []
    
    if guruh:
        query += ' AND guruh = ?'
        params.append(guruh)
    
    if yil:
        query += ' AND tiklangan_yili = ?'
        params.append(yil)
    
    if tur:
        query += ' AND turi = ?'
        params.append(tur)
    
    conn = get_db_connection()
    obidalar = conn.execute(query, params).fetchall()
    
    # Barcha mavjud yillar (asrlar) ro'yxati
    yillar = conn.execute('SELECT DISTINCT tiklangan_yili FROM obidalar WHERE tiklangan_yili IS NOT NULL').fetchall()
    conn.close()
    
    return render_template('filtr.html', 
                           obidalar=obidalar, 
                           yillar=yillar, 
                           tanlangan_guruh=guruh, 
                           tanlangan_yil=yil,
                           tanlangan_tur=tur)

# LOGIN TIZIMI
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_superadmin'] = user['is_superadmin']
            
            flash('Tizimga muvaffaqiyatli kirdingiz', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Login yoki parol noto\'g\'ri', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Tizimdan chiqib ketdingiz', 'success')
    return redirect(url_for('index'))

# ADMIN PANELI
@app.route('/admin')
@login_required
def admin_panel():
    conn = get_db_connection()
    obidalar = conn.execute('SELECT id, nomi, tiklangan_yili, guruh, turi FROM obidalar').fetchall()
    conn.close()
    
    return render_template('admin/panel.html', obidalar=obidalar)

# Obida qo'shish
# Obida qo'shish
@app.route('/admin/obida/add', methods=['GET', 'POST'])
@login_required
def add_obida():
    if request.method == 'POST':
        nomi = request.form['nomi']
        tiklangan_yili = request.form['tiklangan_yili'] or None
        manzili = request.form['manzili']
        qurilish_materiallari = request.form['qurilish_materiallari']
        bosh_fasadi = request.form['bosh_fasadi']
        olchamlari = request.form['olchamlari']
        tarixiy_malumot = request.form['tarixiy_malumot']
        texnik_holati = request.form['texnik_holati']
        guruh = request.form['guruh']
        turi = request.form['turi']
        
        # Rasm yuklash
        rasm_url = None
        if 'rasm' in request.files:
            rasm = request.files['rasm']
            if rasm.filename != '':
                filename = secure_filename(rasm.filename)
                # Rasmlar papkasini tekshirish
                if not os.path.exists('static/uploads'):
                    os.makedirs('static/uploads')
                rasm.save(os.path.join('static/uploads', filename))
                rasm_url = '/static/uploads/' + filename
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO obidalar (nomi, tiklangan_yili, manzili, qurilish_materiallari, 
                                 bosh_fasadi, olchamlari, tarixiy_malumot, texnik_holati, 
                                 guruh, turi, rasm_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, 
              olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, rasm_url))
        conn.commit()
        conn.close()
        
        flash('Yangi obida muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('admin/add_obida.html')

# Obidani tahrirlash
# Obidani tahrirlash
@app.route('/admin/obida/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_obida(id):
    conn = get_db_connection()
    obida = conn.execute('SELECT * FROM obidalar WHERE id = ?', (id,)).fetchone()
    
    if obida is None:
        conn.close()
        flash('Obida topilmadi', 'danger')
        return redirect(url_for('admin_panel'))
    
    # Obidaga tegishli rasmlarni olish
    rasmlar = conn.execute('SELECT * FROM obida_rasmlar WHERE obida_id = ?', (id,)).fetchall()
    
    if request.method == 'POST':
        nomi = request.form['nomi']
        tiklangan_yili = request.form['tiklangan_yili'] or None
        manzili = request.form['manzili']
        qurilish_materiallari = request.form['qurilish_materiallari']
        bosh_fasadi = request.form['bosh_fasadi']
        olchamlari = request.form['olchamlari']
        tarixiy_malumot = request.form['tarixiy_malumot']
        texnik_holati = request.form['texnik_holati']
        guruh = request.form['guruh']
        turi = request.form['turi']
        
        # O'chiriladigan rasmlar
        deleted_images = request.form.getlist('delete_image')
        for img_id in deleted_images:
            if img_id.isdigit():
                conn.execute('DELETE FROM obida_rasmlar WHERE id = ?', (int(img_id),))
        
        # Yangi asosiy rasm (agar mavjud bo'lsa)
        new_main_image = request.form.get('asosiy_rasm')
        if new_main_image and new_main_image.isdigit():
            # Avval barcha rasmlarni asosiy emas qilish
            conn.execute('UPDATE obida_rasmlar SET asosiy = 0 WHERE obida_id = ?', (id,))
            # So'ngra yangi asosiy rasmni belgilash
            main_img_id = int(new_main_image)
            conn.execute('UPDATE obida_rasmlar SET asosiy = 1 WHERE id = ?', (main_img_id,))
            # Obida jadvalidagi asosiy rasmni ham yangilash
            main_img_url = conn.execute('SELECT rasm_url FROM obida_rasmlar WHERE id = ?', (main_img_id,)).fetchone()['rasm_url']
            conn.execute('UPDATE obidalar SET rasm_url = ? WHERE id = ?', (main_img_url, id))
        
        # Rasm izohlarini yangilash
        for rasm in rasmlar:
            izoh_key = f'izoh_{rasm["id"]}'
            if izoh_key in request.form:
                conn.execute('UPDATE obida_rasmlar SET izoh = ? WHERE id = ?', 
                          (request.form[izoh_key], rasm["id"]))
        
        # Yangi rasmlarni yuklash
        rasmlar_files = request.files.getlist('rasmlar')
        if rasmlar_files and rasmlar_files[0].filename:
            # Rasmlar papkasini tekshirish
            if not os.path.exists('static/uploads'):
                os.makedirs('static/uploads')
                
            for index, rasm in enumerate(rasmlar_files):
                if rasm and rasm.filename:
                    filename = secure_filename(f"{id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{index}_{rasm.filename}")
                    rasm_path = os.path.join('static/uploads', filename)
                    rasm.save(rasm_path)
                    rasm_url = '/static/uploads/' + filename
                    
                    # Rasm izohini olish
                    izoh = request.form.get(f'new_izoh_{index}', '')
                    
                    # Rasm jadvaliga saqlash
                    conn.execute('''
                        INSERT INTO obida_rasmlar (obida_id, rasm_url, asosiy, izoh)
                        VALUES (?, ?, 0, ?)
                    ''', (id, rasm_url, izoh))
        
        # Obida ma'lumotlarini yangilash
        conn.execute('''
            UPDATE obidalar 
            SET nomi = ?, tiklangan_yili = ?, manzili = ?, qurilish_materiallari = ?, 
                bosh_fasadi = ?, olchamlari = ?, tarixiy_malumot = ?, texnik_holati = ?, 
                guruh = ?, turi = ?, yangilangan_sana = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (nomi, tiklangan_yili, manzili, qurilish_materiallari, bosh_fasadi, 
              olchamlari, tarixiy_malumot, texnik_holati, guruh, turi, id))
        
        conn.commit()
        conn.close()
        
        flash('Obida muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin_panel'))
    
    conn.close()
    return render_template('admin/edit_obida.html', obida=obida, rasmlar=rasmlar)

# Obidani o'chirish
@app.route('/admin/obida/delete/<int:id>', methods=['POST'])
@login_required
def delete_obida(id):
    conn = get_db_connection()
    obida = conn.execute('SELECT * FROM obidalar WHERE id = ?', (id,)).fetchone()
    
    if obida is None:
        conn.close()
        flash('Obida topilmadi', 'danger')
        return redirect(url_for('admin_panel'))
    
    conn.execute('DELETE FROM obidalar WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Obida muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin_panel'))

# SUPER ADMIN FUNKSIYALARI
@app.route('/superadmin')
@superadmin_required
def superadmin_panel():
    conn = get_db_connection()
    admins = conn.execute('SELECT id, username, is_superadmin, created_at FROM admins').fetchall()
    conn.close()
    
    return render_template('admin/superadmin.html', admins=admins)

# Admin qo'shish
@app.route('/superadmin/admin/add', methods=['GET', 'POST'])
@superadmin_required
def add_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_superadmin = 1 if request.form.get('is_superadmin') else 0
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO admins (username, password, is_superadmin) VALUES (?, ?, ?)',
                      (username, hashed_password, is_superadmin))
            conn.commit()
            flash('Yangi admin muvaffaqiyatli qo\'shildi', 'success')
        except sqlite3.IntegrityError:
            flash('Bu login allaqachon mavjud', 'danger')
        finally:
            conn.close()
            
        return redirect(url_for('superadmin_panel'))
    
    return render_template('admin/add_admin.html')

# Biz haqimizda sahifasi
@app.route('/biz-haqimizda')
def biz_haqimizda():
    return render_template('biz_haqimizda.html')

# Aloqa sahifasi
@app.route('/aloqa', methods=['GET', 'POST'])
def aloqa():
    if request.method == 'POST':
        ism = request.form['ism']
        email = request.form['email']
        telefon = request.form.get('telefon', '')
        mavzu = request.form['mavzu']
        xabar = request.form['xabar']
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO xabarlar (ism, email, telefon, mavzu, xabar)
            VALUES (?, ?, ?, ?, ?)
        ''', (ism, email, telefon, mavzu, xabar))
        conn.commit()
        conn.close()
        
        flash('Xabaringiz muvaffaqiyatli yuborildi', 'success')
        return redirect(url_for('aloqa'))
    
    return render_template('aloqa.html')

# Admin uchun xabarlarni ko'rish sahifasi
@app.route('/admin/xabarlar')
@login_required
def admin_xabarlar():
    conn = get_db_connection()
    xabarlar = conn.execute('SELECT * FROM xabarlar ORDER BY yuborilgan_sana DESC').fetchall()
    conn.close()
    
    # Barcha xabarlar ko'rilganda, session'dagi yangi xabarlar sonini 0 ga o'zgartirish
    session['yangi_xabarlar'] = 0
    
    return render_template('admin/xabarlar.html', xabarlar=xabarlar)

# Xabarni batafsil ko'rish
@app.route('/admin/xabar/<int:id>')
@login_required
def view_xabar(id):
    conn = get_db_connection()
    xabar = conn.execute('SELECT * FROM xabarlar WHERE id = ?', (id,)).fetchone()
    
    if xabar is None:
        conn.close()
        flash('Xabar topilmadi', 'danger')
        return redirect(url_for('admin_xabarlar'))
    
    # Xabarni o'qilgan sifatida belgilash
    if not xabar['oqilgan']:
        conn.execute('UPDATE xabarlar SET oqilgan = 1 WHERE id = ?', (id,))
        conn.commit()
    
    conn.close()
    
    return render_template('admin/view_xabar.html', xabar=xabar)

# Xabarni o'qilgan sifatida belgilash
@app.route('/admin/xabar/<int:id>/oqilgan', methods=['POST'])
@login_required
def xabar_oqilgan(id):
    conn = get_db_connection()
    conn.execute('UPDATE xabarlar SET oqilgan = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Xabar o\'qilgan sifatida belgilandi', 'success')
    return redirect(url_for('admin_xabarlar'))

# Xabarni o'chirish
@app.route('/admin/xabar/<int:id>/delete', methods=['POST'])
@login_required
def delete_xabar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM xabarlar WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Xabar muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin_xabarlar'))

# Adminni o'chirish
@app.route('/superadmin/admin/delete/<int:id>', methods=['POST'])
@superadmin_required
def delete_admin(id):
    # O'zini o'zi o'chirishga yo'l qo'ymaslik
    if id == session['user_id']:
        flash('Siz o\'zingizni o\'chira olmaysiz', 'danger')
        return redirect(url_for('superadmin_panel'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM admins WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Admin muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('superadmin_panel'))

# Ma'lumotlar bazasini inicializatsiya qilish
def init_db():
    conn = get_db_connection()
    
    # Schema faylini ochib, ma'lumotlar bazasini yaratish
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    # Super admin uchun default login/parol (yaratilmagan bo'lsa)
    admin_exists = conn.execute('SELECT COUNT(*) FROM admins WHERE is_superadmin = 1').fetchone()[0]
    if admin_exists == 0:
        hashed_password = generate_password_hash('superadmin')
        conn.execute('INSERT INTO admins (username, password, is_superadmin) VALUES (?, ?, ?)',
                  ('superadmin', hashed_password, 1))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Ma'lumotlar bazasi faylini tekshirish va yaratish
    if not os.path.exists('obidalar.db'):
        with open('schema.sql', 'w') as f:
            with open('database_schema.sql', 'r') as schema_file:
                f.write(schema_file.read())
        init_db()
    
    app.run(debug=True)