from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import time
import csv
import random
from io import StringIO
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'opentrip_flask_secret_key_2026_super_secure'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

def get_db():
    conn = sqlite3.connect('opentrip.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    
    # 1. Users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nama_lengkap TEXT NOT NULL, 
        email TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL, 
        no_whatsapp TEXT, 
        role TEXT DEFAULT 'traveler',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 2. Trips
    cursor.execute('''CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        judul_trip TEXT NOT NULL, 
        destinasi TEXT NOT NULL, 
        harga_per_pax INTEGER NOT NULL, 
        sisa_kuota INTEGER NOT NULL, 
        tanggal_berangkat TEXT NOT NULL, 
        meeting_point TEXT NOT NULL, 
        durasi TEXT NOT NULL, 
        gambar_url TEXT, 
        deskripsi TEXT, 
        fasilitas TEXT, 
        rundown TEXT,
        kategori TEXT DEFAULT 'Bahari'
    )''')
    
    # 3. Bookings
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER NOT NULL, 
        trip_id INTEGER NOT NULL, 
        jumlah_pax INTEGER NOT NULL, 
        total_harga INTEGER NOT NULL, 
        bukti_transfer TEXT, 
        status_pembayaran TEXT DEFAULT 'pending', 
        metode_pembayaran TEXT DEFAULT 'Transfer Bank',
        catatan_pesanan TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (trip_id) REFERENCES trips(id)
    )''')
    
    # 4. Artikel
    cursor.execute('''CREATE TABLE IF NOT EXISTS artikels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        judul TEXT NOT NULL, 
        kategori TEXT NOT NULL, 
        tanggal TEXT NOT NULL, 
        gambar_url TEXT, 
        isi_artikel TEXT,
        author TEXT DEFAULT 'Tim Editorial OP Trip'
    )''')

    # 5. Reviews
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        trip_id INTEGER NOT NULL, 
        nama_user TEXT NOT NULL, 
        rating INTEGER DEFAULT 5, 
        komentar TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 6. Live Chat Messages
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER NOT NULL, 
        room_user_id INTEGER, 
        nama_user TEXT, 
        role TEXT, 
        pesan TEXT, 
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Migration Check
    columns_to_check = [
        ("trips", "kategori", "TEXT DEFAULT 'Bahari'"),
        ("bookings", "metode_pembayaran", "TEXT DEFAULT 'Transfer Bank'"),
        ("bookings", "catatan_pesanan", "TEXT"),
        ("users", "created_at", "TEXT DEFAULT ''"),
        ("messages", "room_user_id", "INTEGER"),
        ("messages", "is_read", "INTEGER DEFAULT 0"),
        ("artikels", "author", "TEXT DEFAULT 'Tim Editorial OP Trip'")
    ]
    for tbl, col, col_type in columns_to_check:
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Ensure Admin Account Exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@opentrip.com'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (nama_lengkap, email, password, no_whatsapp, role) VALUES (?, ?, ?, ?, ?)",
                       ('Admin OP Trip', 'admin@opentrip.com', admin_pass, '081234567890', 'admin'))

    # Seed Sample Trips
    cursor.execute("SELECT COUNT(*) FROM trips")
    if cursor.fetchone()[0] < 3:
        trips_seed = [
            (
                'Sailing Exotic Labuan Bajo', 'Labuan Bajo', 2500000, 8, '25/10/2026', 'Bandara Komodo (LBJ)', '3D2N',
                'https://images.unsplash.com/photo-1516690561799-46d8f74892f1?w=1000&q=80',
                'Jelajahi keajaiban Pulau Komodo, trekking spektakuler di Pulau Padar saat sunrise, berenang di Pink Beach yang magis, dan snorkeling bareng Manta Ray di Taka Makassar.',
                'Kapal Phinisi AC, Kamar Kabin Nyaman, Makan 3x Sehari Chef on Board, Alat Snorkeling Lengkap, Dokumentasi Drone & Mirrorless, Guide Berlisensi HPI, Tiket Masuk TNK',
                'Hari 1: Penjemputan di Bandara Komodo - Check in Kapal - Pulau Kelor - Menikmati Sunset di Pulau Kalong | Hari 2: Sunrise Trekking Pulau Padar - Snorkeling Pink Beach - Berburu Manta di Taka Makassar & Manta Point | Hari 3: Pulau Kanawa - Kembali ke Labuan Bajo & Drop Bandara',
                'Bahari'
            ),
            (
                'Magical Raja Ampat Wayag & Misool', 'Raja Ampat', 4800000, 6, '10/11/2026', 'Bandara DEO Sorong', '4D3N',
                'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=1000&q=80',
                'Surga terumbu karang terbaik di dunia! Saksikan gugusan karst Wayag yang ikonik, berenang di Danau Ubur-ubur tanpa sengat di Misool, dan jelajahi surga bawah laut Papua.',
                'Speedboat Khusus Tour, Resort / Homestay Apung AC, Makan 3x Sehari Menu Seafood Segar, Pin Masuk Konservasi Raja Ampat, Alat Snorkeling & Life Jacket, Dokumentasi Underwater & Drone, Guide Lokal Papua',
                'Hari 1: Penjemputan Bandara Sorong - Nyeberang ke Waisai - Check in Resort - Sunset Pantai Waisai | Hari 2: Eksplor Wayag Karst 1 & 2 - Shark Point - Teluk Kabui | Hari 3: Pasir Timbul Mansuar - Friwen Wall Snorkeling - Yenbuba Village | Hari 4: Belanja Oleh-oleh Sorong - Drop Bandara DEO',
                'Bahari'
            ),
            (
                'Golden Sunrise Bromo & Madakaripura', 'Bromo, Malang', 850000, 14, '01/11/2026', 'Stasiun / Bandara Malang', '2D1N',
                'https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1000&q=80',
                'Menyaksikan pesona matahari terbit di Penanjakan Bromo, menjelajahi Lautan Pasir Berbisik dan Kawah Bromo dengan Jeep 4x4 gagah, serta segarnya Air Terjun Madakaripura.',
                'Jeep Hardtop 4x4 Bromo, Transportasi AC Antar Jemput Malang/Surabaya, Tiket Masuk Taman Nasional Bromo & Madakaripura, Penginapan 1 Malam, Makan 2x, Ojek Madakaripura, Tour Leader & Dokumentasi',
                'Hari 1: Penjemputan Malang/Surabaya - Wisata Air Terjun Madakaripura - Check in Penginapan Bromo - Istirahat | Hari 2: 03.00 Jeep Tour Menuju Sunrise Point Penanjakan - Kawah Bromo & Pura Luhur Poten - Pasir Berbisik & Savana Bukit Teletubbies - Kembali ke Malang',
                'Pegunungan'
            )
        ]
        for t in trips_seed:
            cursor.execute('''INSERT OR IGNORE INTO trips 
                (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url, deskripsi, fasilitas, rundown, kategori)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', t)

    # Seed Sample Articles
    cursor.execute("SELECT COUNT(*) FROM artikels")
    if cursor.fetchone()[0] < 3:
        artikels_seed = [
            (
                '5 Barang Wajib Saat Open Trip Island Hopping', 'Travel Guide', '15/09/2026',
                'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&q=80',
                'Persiapan barang bawaan sangat vital saat mengikuti Open Trip jelajah pulau. Pastikan membawa dry bag tahan air, sunscreen ramah terumbu karang (reef-safe) minimal SPF 50+, kacamata hitam UV protection, sandal gunung anti-slip, dan obat antimual perjalanan laut.',
                'Tim Editorial OP Trip'
            ),
            (
                'Tips Berburu Golden Sunrise Spektakuler di Puncak Bromo', 'Tips Wisata', '22/09/2026',
                'https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=800&q=80',
                'Suhu di Bromo saat dini hari bisa mencapai 5-8 derajat celcius. Kenakan jaket windproof berlapis, sarung tangan tebal, dan kupluk hangat. Datanglah ke spot Penanjakan 1 atau Bukit Kingkong lebih awal sekitar pukul 04.00 WIB untuk mendapatkan sudut foto terbaik menghadap Gunung Batok dan Semeru.',
                'Rangga Pratama (Guide Bromo)'
            )
        ]
        for a in artikels_seed:
            cursor.execute('''INSERT OR IGNORE INTO artikels (judul, kategori, tanggal, gambar_url, isi_artikel, author)
                              VALUES (?, ?, ?, ?, ?, ?)''', a)

    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def format_to_ddmmyyyy(raw_date):
    if not raw_date:
        return ''
    try:
        return datetime.strptime(raw_date, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError:
        return raw_date

def get_rekap_pendapatan():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status_pembayaran = 'lunas' THEN total_harga ELSE 0 END), SUM(CASE WHEN status_pembayaran = 'lunas' THEN 1 ELSE 0 END), SUM(CASE WHEN status_pembayaran = 'pending' THEN 1 ELSE 0 END) FROM bookings")
    row_all = cursor.fetchone()
    total_all_omset = row_all[1] or 0
    total_all_lunas = row_all[2] or 0
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status_pembayaran = 'lunas' THEN total_harga ELSE 0 END), SUM(CASE WHEN status_pembayaran = 'lunas' THEN 1 ELSE 0 END) FROM bookings WHERE date(created_at) = ?", (today_str,))
    row_today = cursor.fetchone()

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status_pembayaran = 'lunas' THEN total_harga ELSE 0 END), SUM(CASE WHEN status_pembayaran = 'lunas' THEN 1 ELSE 0 END) FROM bookings WHERE date(created_at) >= ?", (seven_days_ago,))
    row_week = cursor.fetchone()

    month_str = datetime.now().strftime('%Y-%m')
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status_pembayaran = 'lunas' THEN total_harga ELSE 0 END), SUM(CASE WHEN status_pembayaran = 'lunas' THEN 1 ELSE 0 END) FROM bookings WHERE strftime('%Y-%m', created_at) = ?", (month_str,))
    row_month = cursor.fetchone()

    year_str = datetime.now().strftime('%Y')
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status_pembayaran = 'lunas' THEN total_harga ELSE 0 END), SUM(CASE WHEN status_pembayaran = 'lunas' THEN 1 ELSE 0 END) FROM bookings WHERE strftime('%Y', created_at) = ?", (year_str,))
    row_year = cursor.fetchone()

    avg_lunas = int(total_all_omset / total_all_lunas) if total_all_lunas > 0 else 0
    conn.close()

    return {
        'all': {'omset': total_all_omset, 'bookings': row_all[0] or 0, 'lunas': total_all_lunas, 'pending': row_all[3] or 0, 'avg': avg_lunas},
        'today': {'omset': row_today[1] or 0, 'bookings': row_today[0] or 0, 'lunas': row_today[2] or 0, 'label': datetime.now().strftime('%d %B %Y')},
        'week': {'omset': row_week[1] or 0, 'bookings': row_week[0] or 0, 'lunas': row_week[2] or 0, 'label': '7 Hari Terakhir'},
        'month': {'omset': row_month[1] or 0, 'bookings': row_month[0] or 0, 'lunas': row_month[2] or 0, 'label': datetime.now().strftime('%B %Y')},
        'year': {'omset': row_year[1] or 0, 'bookings': row_year[0] or 0, 'lunas': row_year[2] or 0, 'label': f'Tahun {year_str}'}
    }

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next') or request.form.get('next') or ''

    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(next_page if next_page else url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['nama_lengkap'] = user['nama_lengkap']
            session['role'] = user['role']
            session['email'] = user['email']
            session['no_whatsapp'] = user['no_whatsapp']
            conn.close()
            
            flash(f"Selamat datang kembali, {user['nama_lengkap']}! 👋", 'success')
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Email atau kata sandi tidak cocok. Silakan coba lagi.', 'danger')
            
    # Ambil 1 trip terbaru dari database untuk ditampilkan di hero login
    cursor.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 1")
    featured_trip = cursor.fetchone()
    conn.close()

    return render_template('auth/login.html', next=next_page, featured_trip=featured_trip)

@app.route('/register', methods=['GET', 'POST'])
def register():
    next_page = request.args.get('next') or request.form.get('next') or ''

    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        nama = request.form.get('nama_lengkap', '').strip()
        email = request.form.get('email', '').strip().lower()
        no_wa = request.form.get('no_whatsapp', '').strip()
        password = request.form.get('password', '')

        if not (nama and email and password):
            flash('Harap lengkapi semua kolom yang wajib diisi.', 'danger')
        else:
            hashed_pass = generate_password_hash(password)
            try:
                cursor.execute("INSERT INTO users (nama_lengkap, email, password, no_whatsapp, role) VALUES (?, ?, ?, ?, 'traveler')",
                               (nama, email, hashed_pass, no_wa))
                conn.commit()
                
                # Auto Login setelah register
                cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
                new_user = cursor.fetchone()
                
                session['user_id'] = new_user['id']
                session['nama_lengkap'] = new_user['nama_lengkap']
                session['role'] = new_user['role']
                session['email'] = new_user['email']
                session['no_whatsapp'] = new_user['no_whatsapp']
                conn.close()

                flash('Pendaftaran berhasil! Akun kamu otomatis aktif.', 'success')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash('Alamat email sudah terdaftar. Silakan login.', 'danger')

    cursor.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 1")
    featured_trip = cursor.fetchone()
    conn.close()

    return render_template('auth/register.html', next=next_page, featured_trip=featured_trip)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    conn = get_db()
    cursor = conn.cursor()
    
    step = request.args.get('step', 'request')
    email_session = session.get('reset_email', '')

    if request.method == 'POST':
        action = request.form.get('action')

        # STEP 1: Minta Kode OTP
        if action == 'send_otp':
            email = request.form.get('email', '').strip().lower()
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
            user = cursor.fetchone()

            if user:
                otp_code = str(random.randint(100000, 999999))
                session['reset_email'] = email
                session['reset_otp'] = otp_code
                flash(f'Kode OTP berhasil dikirim! Kode Demo kamu: {otp_code}', 'info')
                
                cursor.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 1")
                featured_trip = cursor.fetchone()
                conn.close()
                return render_template('auth/forgot.html', step='verify', email=email, featured_trip=featured_trip)
            else:
                flash('Alamat email tidak ditemukan dalam sistem.', 'danger')

        # STEP 2: Verifikasi OTP & Simpan Password Baru
        elif action == 'verify_otp':
            otp_input = request.form.get('otp', '').strip()
            new_password = request.form.get('password', '')
            email = session.get('reset_email')
            saved_otp = session.get('reset_otp')

            if not email or not saved_otp:
                flash('Sesi pemulihan kadaluarsa. Silakan minta kode OTP kembali.', 'danger')
                step = 'request'
            elif otp_input != saved_otp:
                flash('Kode OTP tidak valid! Silakan periksa kembali.', 'danger')
                cursor.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 1")
                featured_trip = cursor.fetchone()
                conn.close()
                return render_template('auth/forgot.html', step='verify', email=email, featured_trip=featured_trip)
            else:
                cursor.execute("UPDATE users SET password = ? WHERE LOWER(email) = ?", 
                               (generate_password_hash(new_password), email))
                conn.commit()
                session.pop('reset_email', None)
                session.pop('reset_otp', None)
                conn.close()
                flash('Kata sandi berhasil diperbarui! Silakan masuk dengan sandi baru.', 'success')
                return redirect(url_for('login'))

    cursor.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 1")
    featured_trip = cursor.fetchone()
    conn.close()

    return render_template('auth/forgot.html', step=step, email=email_session, featured_trip=featured_trip)

@app.route('/logout')
def logout():
    session.clear()
    flash('Kamu telah keluar dari akun.', 'info')
    return redirect(url_for('dashboard'))

# --- PUBLIC ROUTES (GUEST & LOGGED USER) ---
@app.route('/')
@app.route('/dashboard')
def dashboard():
    search = request.args.get('search', '').strip()
    destinasi_filter = request.args.get('destinasi', '').strip()
    kategori_filter = request.args.get('kategori', '').strip()
    sort_filter = request.args.get('sort', 'newest').strip()
    
    query = "SELECT * FROM trips WHERE 1=1"
    params = []
    
    if search:
        query += " AND (judul_trip LIKE ? OR destinasi LIKE ? OR deskripsi LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if destinasi_filter:
        query += " AND destinasi LIKE ?"
        params.append(f"%{destinasi_filter}%")
    if kategori_filter:
        query += " AND (kategori LIKE ? OR judul_trip LIKE ?)"
        params.extend([f"%{kategori_filter}%", f"%{kategori_filter}%"])
        
    if sort_filter == 'price_asc':
        query += " ORDER BY harga_per_pax ASC"
    elif sort_filter == 'price_desc':
        query += " ORDER BY harga_per_pax DESC"
    elif sort_filter == 'quota':
        query += " ORDER BY sisa_kuota ASC"
    else:
        query += " ORDER BY id DESC"
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    trips = cursor.fetchall()
    
    cursor.execute("SELECT * FROM artikels ORDER BY id DESC LIMIT 4")
    artikels = cursor.fetchall()

    cursor.execute("SELECT DISTINCT destinasi FROM trips LIMIT 8")
    destinations = [r['destinasi'] for r in cursor.fetchall()]

    my_bookings_count = 0
    if 'user_id' in session:
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ?", (session['user_id'],))
        my_bookings_count = cursor.fetchone()[0]
    
    conn.close()

    return render_template('user_dashboard.html', 
                           trips=trips, 
                           artikels=artikels, 
                           destinations=destinations,
                           search=search, 
                           destinasi_filter=destinasi_filter, 
                           kategori_filter=kategori_filter,
                           sort_filter=sort_filter,
                           my_bookings_count=my_bookings_count)

@app.route('/trip/<int:trip_id>', methods=['GET', 'POST'])
def trip_detail(trip_id):
    conn = get_db()
    cursor = conn.cursor()

    # Kirim ulasan review (harus login)
    if request.method == 'POST':
        if 'user_id' not in session:
            conn.close()
            flash('Silakan masuk terlebih dahulu untuk menulis ulasan.', 'warning')
            return redirect(url_for('login', next=url_for('trip_detail', trip_id=trip_id)))

        rating = int(request.form.get('rating', 5))
        komentar = request.form.get('komentar', '').strip()
        if komentar:
            cursor.execute("INSERT INTO reviews (trip_id, nama_user, rating, komentar) VALUES (?, ?, ?, ?)",
                           (trip_id, session['nama_lengkap'], rating, komentar))
            conn.commit()
            flash('Terima kasih atas ulasan dan rating kamu! 🌟', 'success')
            conn.close()
            return redirect(url_for('trip_detail', trip_id=trip_id))

    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip: 
        conn.close()
        flash('Paket trip tidak ditemukan.', 'danger')
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM reviews WHERE trip_id = ? ORDER BY id DESC", (trip_id,))
    reviews = cursor.fetchall()
    
    cursor.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE trip_id = ?", (trip_id,))
    stat = cursor.fetchone()
    avg_rating = round(stat[0], 1) if stat[0] else 4.9
    total_reviews = stat[1] if stat[1] else 0

    fasilitas_list = [f.strip() for f in trip['fasilitas'].split(',') if f.strip()] if trip['fasilitas'] else []
    
    rundown_raw = trip['rundown'] or ''
    rundown_items = []
    parts = rundown_raw.split('|') if '|' in rundown_raw else (rundown_raw.split('\n') if '\n' in rundown_raw else [rundown_raw])
        
    for p in parts:
        p = p.strip()
        if not p: continue
        if ':' in p:
            h, d = p.split(':', 1)
            rundown_items.append({'hari': h.strip(), 'desc': d.strip()})
        else:
            rundown_items.append({'hari': f'Aktivitas {len(rundown_items)+1}', 'desc': p})

    cursor.execute("SELECT * FROM trips WHERE id != ? LIMIT 3", (trip_id,))
    related_trips = cursor.fetchall()
    conn.close()
    
    return render_template('trip_detail.html', 
                           trip=trip, 
                           reviews=reviews, 
                           avg_rating=avg_rating,
                           total_reviews=total_reviews,
                           fasilitas_list=fasilitas_list,
                           rundown_items=rundown_items,
                           related_trips=related_trips)

@app.route('/artikel/<int:artikel_id>')
def artikel_detail(artikel_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM artikels WHERE id = ?", (artikel_id,))
    artikel = cursor.fetchone()
    
    if not artikel: 
        conn.close()
        flash('Artikel tidak ditemukan.', 'danger')
        return redirect(url_for('dashboard'))
        
    cursor.execute("SELECT * FROM artikels WHERE id != ? ORDER BY id DESC LIMIT 4", (artikel_id,))
    semua_artikel = cursor.fetchall()
    conn.close()
    
    return render_template('artikel_detail.html', artikel=artikel, semua_artikel=semua_artikel)

# --- PROTECTED USER ROUTES ---
@app.route('/checkout/<int:trip_id>', methods=['GET', 'POST'])
def checkout(trip_id):
    if 'user_id' not in session: 
        flash('Silakan masuk terlebih dahulu untuk melakukan reservasi.', 'info')
        return redirect(url_for('login', next=request.path))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip:
        conn.close()
        flash('Paket trip tidak ditemukan.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        jumlah_pax = int(request.form.get('jumlah_pax', 1))
        metode_bayar = request.form.get('metode_pembayaran', 'Transfer Bank BCA')
        catatan = request.form.get('catatan_pesanan', '').strip()
        
        if jumlah_pax < 1 or jumlah_pax > trip['sisa_kuota']:
            flash(f'Jumlah pax tidak valid! Kuota tersisa {trip["sisa_kuota"]} pax.', 'danger')
            conn.close()
            return redirect(url_for('checkout', trip_id=trip_id))
            
        file = request.files.get('bukti_transfer')
        filename = ''
        if file and file.filename:
            filename = f"transfer_{int(time.time())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        total_harga = jumlah_pax * trip['harga_per_pax']
        
        cursor.execute('''
            INSERT INTO bookings (user_id, trip_id, jumlah_pax, total_harga, bukti_transfer, status_pembayaran, metode_pembayaran, catatan_pesanan) 
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        ''', (session['user_id'], trip_id, jumlah_pax, total_harga, filename, metode_bayar, catatan))
        booking_id = cursor.lastrowid
        
        cursor.execute("UPDATE trips SET sisa_kuota = sisa_kuota - ? WHERE id = ?", (jumlah_pax, trip_id))
        conn.commit()
        conn.close()
        
        return render_template('checkout.html', berhasil=True, booking_id=booking_id, trip=trip, jumlah_pax=jumlah_pax, total_harga=total_harga)
        
    conn.close()
    return render_template('checkout.html', trip=trip, berhasil=False)

@app.route('/riwayat')
def riwayat():
    if 'user_id' not in session:
        flash('Silakan masuk terlebih dahulu untuk melihat riwayat pesanan.', 'info')
        return redirect(url_for('login', next=request.path))
        
    status_filter = request.args.get('status', 'all').strip().lower()
    
    query = '''
        SELECT bookings.id, trips.judul_trip, trips.destinasi, trips.tanggal_berangkat, 
               trips.meeting_point, bookings.jumlah_pax, bookings.total_harga, 
               bookings.bukti_transfer, bookings.status_pembayaran, bookings.created_at,
               trips.gambar_url, trips.durasi, trips.id as trip_id,
               bookings.metode_pembayaran, bookings.catatan_pesanan
        FROM bookings
        LEFT JOIN trips ON bookings.trip_id = trips.id
        WHERE bookings.user_id = ?
    '''
    params = [session['user_id']]
    
    if status_filter in ['lunas', 'pending', 'batal']:
        query += " AND bookings.status_pembayaran = ?"
        params.append(status_filter)
        
    query += " ORDER BY bookings.id DESC"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    my_bookings = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ?", (session['user_id'],))
    count_all = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status_pembayaran = 'lunas'", (session['user_id'],))
    count_lunas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ? AND status_pembayaran = 'pending'", (session['user_id'],))
    count_pending = cursor.fetchone()[0]

    conn.close()
    
    return render_template('riwayat.html', 
                           bookings=my_bookings, 
                           status_filter=status_filter,
                           count_all=count_all,
                           count_lunas=count_lunas,
                           count_pending=count_pending)

@app.route('/invoice/<int:booking_id>')
def invoice(booking_id):
    if 'user_id' not in session:
        flash('Silakan masuk terlebih dahulu.', 'info')
        return redirect(url_for('login', next=request.path))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bookings.*, 
               users.nama_lengkap, users.email, users.no_whatsapp,
               trips.judul_trip, trips.destinasi, trips.tanggal_berangkat, 
               trips.meeting_point, trips.durasi, trips.harga_per_pax, trips.gambar_url,
               trips.fasilitas
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        LEFT JOIN trips ON bookings.trip_id = trips.id
        WHERE bookings.id = ?
    ''', (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    
    if not booking:
        flash('Invoice tidak ditemukan.', 'danger')
        return redirect(url_for('dashboard'))
        
    if session.get('role') != 'admin' and booking['user_id'] != session['user_id']:
        flash('Akses invoice tidak diizinkan.', 'danger')
        return redirect(url_for('riwayat'))
        
    ref_code = f"OPT-{datetime.strptime(booking['created_at'][:10], '%Y-%m-%d').strftime('%Y%m')}-{booking['id']:05d}"
    return render_template('invoice.html', booking=booking, ref_code=ref_code)

# --- ADMIN DASHBOARD & CRUD ROUTES ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Akses khusus administrator!', 'danger')
        return redirect(url_for('login'))
        
    active_tab = request.args.get('tab', 'rekap')
    period = request.args.get('period', 'all')
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all').strip()

    conn = get_db()
    cursor = conn.cursor()
    rekap = get_rekap_pendapatan()

    cursor.execute("SELECT COUNT(*) FROM trips")
    total_trips = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'traveler'")
    total_travelers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM artikels")
    total_artikels = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM trips ORDER BY id DESC")
    trips = cursor.fetchall()

    cursor.execute("SELECT * FROM artikels ORDER BY id DESC")
    artikels = cursor.fetchall()
    
    b_query = '''
        SELECT bookings.id, users.nama_lengkap, users.email, users.no_whatsapp, trips.judul_trip, 
               trips.destinasi, bookings.jumlah_pax, bookings.total_harga, bookings.bukti_transfer, 
               bookings.status_pembayaran, bookings.metode_pembayaran, bookings.catatan_pesanan, bookings.created_at
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        LEFT JOIN trips ON bookings.trip_id = trips.id
        WHERE 1=1
    '''
    b_params = []
    if search_q:
        b_query += " AND (users.nama_lengkap LIKE ? OR trips.judul_trip LIKE ? OR users.no_whatsapp LIKE ?)"
        b_params.extend([f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"])
    if status_filter in ['lunas', 'pending', 'ditolak']:
        b_query += " AND bookings.status_pembayaran = ?"
        b_params.append(status_filter)
        
    b_query += " ORDER BY bookings.id DESC"
    cursor.execute(b_query, b_params)
    bookings = cursor.fetchall()

    cursor.execute('''
        SELECT users.id, users.nama_lengkap, users.email, users.no_whatsapp, users.role, users.created_at,
               (SELECT COUNT(*) FROM bookings WHERE user_id = users.id) as total_pesanan,
               (SELECT SUM(total_harga) FROM bookings WHERE user_id = users.id AND status_pembayaran = 'lunas') as total_spend
        FROM users
        ORDER BY users.id DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    
    return render_template('admin/admin_dashboard.html', 
                           rekap=rekap, period=period, active_tab=active_tab,
                           total_trips=total_trips, total_bookings=total_bookings, 
                           total_travelers=total_travelers, total_artikels=total_artikels,
                           trips=trips, artikels=artikels, bookings=bookings, users=users,
                           search_q=search_q, status_filter=status_filter)

@app.route('/admin/add-trip', methods=['POST'])
def admin_add_trip():
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    judul = request.form.get('judul_trip', '').strip()
    destinasi = request.form.get('destinasi', '').strip()
    kategori = request.form.get('kategori', 'Bahari').strip()
    
    harga_raw = request.form.get('harga_per_pax', '0').replace('.', '').replace(',', '').strip()
    harga = int(harga_raw) if harga_raw.isdigit() else 0
    kuota = int(request.form.get('sisa_kuota', 10))
    
    tanggal = format_to_ddmmyyyy(request.form.get('tanggal_berangkat', ''))
    mepo = request.form.get('meeting_point', '').strip()
    durasi = request.form.get('durasi', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    fasilitas = request.form.get('fasilitas', '').strip()
    rundown = request.form.get('rundown', '').strip()
    
    file = request.files.get('gambar_file')
    url_input = request.form.get('gambar_url', '').strip()
    
    if file and file.filename:
        filename = f"trip_{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        gambar = filename
    elif url_input:
        gambar = url_input
    else:
        gambar = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800'
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trips (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url, deskripsi, fasilitas, rundown, kategori)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (judul, destinasi, harga, kuota, tanggal, mepo, durasi, gambar, deskripsi, fasilitas, rundown, kategori))
    conn.commit()
    conn.close()
    
    flash('Paket Open Trip baru berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_dashboard', tab='trips'))

@app.route('/admin/edit-trip/<int:trip_id>', methods=['POST'])
def admin_edit_trip(trip_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    judul = request.form.get('judul_trip', '').strip()
    destinasi = request.form.get('destinasi', '').strip()
    kategori = request.form.get('kategori', 'Bahari').strip()
    
    harga_raw = request.form.get('harga_per_pax', '0').replace('.', '').replace(',', '').strip()
    harga = int(harga_raw) if harga_raw.isdigit() else 0
    kuota = int(request.form.get('sisa_kuota', 10))
    
    tanggal = format_to_ddmmyyyy(request.form.get('tanggal_berangkat', ''))
    mepo = request.form.get('meeting_point', '').strip()
    durasi = request.form.get('durasi', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    fasilitas = request.form.get('fasilitas', '').strip()
    rundown = request.form.get('rundown', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT gambar_url FROM trips WHERE id = ?", (trip_id,))
    existing = cursor.fetchone()
    current_gambar = existing['gambar_url'] if existing else ''
    
    file = request.files.get('gambar_file')
    url_input = request.form.get('gambar_url', '').strip()
    
    if file and file.filename:
        filename = f"trip_{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        gambar = filename
    elif url_input:
        gambar = url_input
    else:
        gambar = current_gambar

    cursor.execute('''
        UPDATE trips 
        SET judul_trip = ?, destinasi = ?, harga_per_pax = ?, sisa_kuota = ?, 
            tanggal_berangkat = ?, meeting_point = ?, durasi = ?, gambar_url = ?, 
            deskripsi = ?, fasilitas = ?, rundown = ?, kategori = ?
        WHERE id = ?
    ''', (judul, destinasi, harga, kuota, tanggal, mepo, durasi, gambar, deskripsi, fasilitas, rundown, kategori, trip_id))
    conn.commit()
    conn.close()
    
    flash('Perubahan paket trip berhasil disimpan!', 'success')
    return redirect(url_for('admin_dashboard', tab='trips'))

@app.route('/admin/delete-trip/<int:trip_id>')
def admin_delete_trip(trip_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()
    
    flash('Paket trip berhasil dihapus.', 'info')
    return redirect(url_for('admin_dashboard', tab='trips'))

@app.route('/admin/add-artikel', methods=['POST'])
def admin_add_artikel():
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
    
    judul = request.form.get('judul', '').strip()
    kategori = request.form.get('kategori', 'Travel Guide').strip()
    tanggal = format_to_ddmmyyyy(request.form.get('tanggal', ''))
    isi = request.form.get('isi_artikel', '').strip()
    author = request.form.get('author', 'Tim Editorial OP Trip').strip()
    
    file = request.files.get('gambar_file')
    url_input = request.form.get('gambar_url', '').strip()
    
    if file and file.filename:
        filename = f"artikel_{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        gambar = filename
    elif url_input:
        gambar = url_input
    else:
        gambar = 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800'
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO artikels (judul, kategori, tanggal, gambar_url, isi_artikel, author) VALUES (?, ?, ?, ?, ?, ?)",
                   (judul, kategori, tanggal, gambar, isi, author))
    conn.commit()
    conn.close()
    
    flash('Artikel panduan wisata berhasil diterbitkan!', 'success')
    return redirect(url_for('admin_dashboard', tab='artikels'))

@app.route('/admin/edit-artikel/<int:artikel_id>', methods=['POST'])
def admin_edit_artikel(artikel_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    judul = request.form.get('judul', '').strip()
    kategori = request.form.get('kategori', 'Travel Guide').strip()
    tanggal = format_to_ddmmyyyy(request.form.get('tanggal', ''))
    isi = request.form.get('isi_artikel', '').strip()
    author = request.form.get('author', 'Tim Editorial OP Trip').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT gambar_url FROM artikels WHERE id = ?", (artikel_id,))
    existing = cursor.fetchone()
    current_gambar = existing['gambar_url'] if existing else ''
    
    file = request.files.get('gambar_file')
    url_input = request.form.get('gambar_url', '').strip()
    
    if file and file.filename:
        filename = f"artikel_{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        gambar = filename
    elif url_input:
        gambar = url_input
    else:
        gambar = current_gambar

    cursor.execute('''
        UPDATE artikels 
        SET judul = ?, kategori = ?, tanggal = ?, gambar_url = ?, isi_artikel = ?, author = ?
        WHERE id = ?
    ''', (judul, kategori, tanggal, gambar, isi, author, artikel_id))
    conn.commit()
    conn.close()
    
    flash('Artikel berhasil diperbarui!', 'success')
    return redirect(url_for('admin_dashboard', tab='artikels'))

@app.route('/admin/delete-artikel/<int:artikel_id>')
def admin_delete_artikel(artikel_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM artikels WHERE id = ?", (artikel_id,))
    conn.commit()
    conn.close()
    
    flash('Artikel berhasil dihapus.', 'info')
    return redirect(url_for('admin_dashboard', tab='artikels'))

@app.route('/admin/update-booking/<int:booking_id>/<string:status>')
def admin_update_booking(booking_id, status):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    valid_statuses = ['lunas', 'pending', 'ditolak']
    if status not in valid_statuses:
        flash('Status tidak valid.', 'danger')
        return redirect(url_for('admin_dashboard', tab='bookings'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status_pembayaran = ? WHERE id = ?", (status, booking_id))
    conn.commit()
    conn.close()
    
    if status == 'lunas':
        flash(f'Pesanan #{booking_id} BERHASIL DIKONFIRMASI LUNAS!', 'success')
    elif status == 'pending':
        flash(f'Status pesanan #{booking_id} dikembalikan ke PENDING.', 'info')
    else:
        flash(f'Pesanan #{booking_id} telah DITOLAK.', 'danger')
        
    return redirect(url_for('admin_dashboard', tab='bookings'))

@app.route('/admin/user/toggle-role/<int:target_user_id>')
def admin_toggle_role(target_user_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    if target_user_id == session['user_id']:
        flash('Tidak dapat mengubah peran akun diri sendiri.', 'danger')
        return redirect(url_for('admin_dashboard', tab='users'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role, nama_lengkap FROM users WHERE id = ?", (target_user_id,))
    target = cursor.fetchone()
    
    if target:
        new_role = 'traveler' if target['role'] == 'admin' else 'admin'
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, target_user_id))
        conn.commit()
        flash(f"Peran pengguna {target['nama_lengkap']} berhasil diubah menjadi {new_role.upper()}.", 'success')
    conn.close()
    
    return redirect(url_for('admin_dashboard', tab='users'))

@app.route('/admin/user/delete/<int:target_user_id>')
def admin_delete_user(target_user_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    if target_user_id == session['user_id']:
        flash('Tidak dapat menghapus akun admin yang sedang aktif.', 'danger')
        return redirect(url_for('admin_dashboard', tab='users'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
    cursor.execute("DELETE FROM bookings WHERE user_id = ?", (target_user_id,))
    cursor.execute("DELETE FROM messages WHERE room_user_id = ?", (target_user_id,))
    conn.commit()
    conn.close()
    
    flash('Data pengguna berhasil dihapus.', 'info')
    return redirect(url_for('admin_dashboard', tab='users'))

@app.route('/admin/manifest/<int:trip_id>')
def admin_trip_manifest(trip_id):
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Ambil data detail trip
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip:
        conn.close()
        flash('Paket trip tidak ditemukan.', 'danger')
        return redirect(url_for('admin_dashboard', tab='trips'))
        
    # Ambil daftar peserta dengan status pembayaran LUNAS
    cursor.execute('''
        SELECT bookings.id as booking_id, bookings.jumlah_pax, bookings.total_harga, 
               bookings.catatan_pesanan, bookings.created_at,
               users.nama_lengkap, users.no_whatsapp, users.email
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        WHERE bookings.trip_id = ? AND bookings.status_pembayaran = 'lunas'
        ORDER BY bookings.id ASC
    ''', (trip_id,))
    peserta = cursor.fetchall()
    
    total_pax_terisi = sum(p['jumlah_pax'] for p in peserta)
    conn.close()
    
    return render_template('admin/manifest.html', trip=trip, peserta=peserta, total_pax_terisi=total_pax_terisi)

# --- EXPORT EXCEL & PDF ---
@app.route('/admin/export/excel')
def export_excel():
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    period = request.args.get('period', 'all')
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT bookings.id, bookings.created_at, users.nama_lengkap, users.email, users.no_whatsapp, 
               trips.judul_trip, trips.destinasi, bookings.jumlah_pax, bookings.total_harga, 
               bookings.metode_pembayaran, bookings.status_pembayaran
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        LEFT JOIN trips ON bookings.trip_id = trips.id
        WHERE 1=1
    '''
    params = []
    
    if period == 'today':
        query += " AND date(bookings.created_at) = date('now', 'localtime')"
        filename_period = f"Hari_Ini_{datetime.now().strftime('%Y%m%d')}"
    elif period == 'week':
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        query += " AND date(bookings.created_at) >= ?"
        params.append(seven_days_ago)
        filename_period = f"Minggu_Ini_{datetime.now().strftime('%Y%m%d')}"
    elif period == 'month':
        month_str = datetime.now().strftime('%Y-%m')
        query += " AND strftime('%Y-%m', bookings.created_at) = ?"
        params.append(month_str)
        filename_period = f"Bulan_{month_str}"
    elif period == 'year':
        year_str = datetime.now().strftime('%Y')
        query += " AND strftime('%Y', bookings.created_at) = ?"
        params.append(year_str)
        filename_period = f"Tahun_{year_str}"
    else:
        filename_period = "Semua_Waktu"
        
    query += " ORDER BY bookings.id DESC"
    cursor.execute(query, params)
    bookings = cursor.fetchall()
    conn.close()

    si = StringIO()
    si.write('\ufeff')
    cw = csv.writer(si)
    
    cw.writerow(['REKAP LAPORAN PENDAPATAN & PEMESANAN — OP TRIP INDONESIA'])
    cw.writerow([f'Periode: {filename_period}', f'Tanggal Unduh: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'])
    cw.writerow([])
    cw.writerow(['No Booking', 'Waktu Transaksi', 'Nama Pemesan', 'Email', 'No WhatsApp', 'Paket Trip', 'Destinasi', 'Pax', 'Total Tagihan (Rp)', 'Metode Bayar', 'Status Pembayaran'])
    
    total_lunas = 0
    for b in bookings:
        if b['status_pembayaran'] == 'lunas':
            total_lunas += b['total_harga']
        cw.writerow([
            f"OPT-{b['id']:05d}",
            b['created_at'],
            b['nama_lengkap'],
            b['email'],
            b['no_whatsapp'],
            b['judul_trip'],
            b['destinasi'],
            b['jumlah_pax'],
            b['total_harga'],
            b['metode_pembayaran'] or 'Transfer Bank',
            b['status_pembayaran'].upper()
        ])
        
    cw.writerow([])
    cw.writerow(['TOTAL OMSET LUNAS (Rp)', '', '', '', '', '', '', '', total_lunas, '', ''])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=Laporan_OP_Trip_{filename_period}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

@app.route('/admin/export/pdf')
def export_pdf():
    if 'user_id' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    period = request.args.get('period', 'all')
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT bookings.id, bookings.created_at, users.nama_lengkap, users.email, users.no_whatsapp, 
               trips.judul_trip, trips.destinasi, bookings.jumlah_pax, bookings.total_harga, 
               bookings.metode_pembayaran, bookings.status_pembayaran
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        LEFT JOIN trips ON bookings.trip_id = trips.id
        WHERE 1=1
    '''
    params = []
    
    if period == 'today':
        query += " AND date(bookings.created_at) = date('now', 'localtime')"
        period_title = f"Hari Ini ({datetime.now().strftime('%d %B %Y')})"
    elif period == 'week':
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        query += " AND date(bookings.created_at) >= ?"
        params.append(seven_days_ago)
        period_title = "7 Hari Terakhir (Minggu Ini)"
    elif period == 'month':
        month_str = datetime.now().strftime('%Y-%m')
        query += " AND strftime('%Y-%m', bookings.created_at) = ?"
        params.append(month_str)
        period_title = f"Bulan {datetime.now().strftime('%B %Y')}"
    elif period == 'year':
        year_str = datetime.now().strftime('%Y')
        query += " AND strftime('%Y', bookings.created_at) = ?"
        params.append(year_str)
        period_title = f"Tahun {year_str}"
    else:
        period_title = "Semua Waktu (Keseluruhan)"
        
    query += " ORDER BY bookings.id DESC"
    cursor.execute(query, params)
    bookings = cursor.fetchall()
    
    total_omset = sum(b['total_harga'] for b in bookings if b['status_pembayaran'] == 'lunas')
    total_lunas = sum(1 for b in bookings if b['status_pembayaran'] == 'lunas')
    total_pending = sum(1 for b in bookings if b['status_pembayaran'] == 'pending')
    conn.close()

    return render_template('admin/export_pdf.html', 
                           bookings=bookings, 
                           total_omset=total_omset, 
                           total_lunas=total_lunas,
                           total_pending=total_pending,
                           period_title=period_title,
                           now_str=datetime.now().strftime('%d %B %Y, %H:%M WIB'))

# --- LIVE CHAT API ---
@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json or request.form
    pesan = data.get('pesan', '').strip()
    
    if not pesan:
        return jsonify({'status': 'error', 'message': 'Pesan tidak boleh kosong'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    
    if session.get('role') == 'admin':
        room_user_id = data.get('target_user_id')
        if not room_user_id:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Target traveler tidak dipilih'}), 400
        room_user_id = int(room_user_id)
    else:
        room_user_id = session['user_id']
        
    cursor.execute("""
        INSERT INTO messages (user_id, room_user_id, nama_user, role, pesan, is_read) 
        VALUES (?, ?, ?, ?, ?, 0)
    """, (session['user_id'], room_user_id, session['nama_lengkap'], session['role'], pesan))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/chat/list')
def chat_list():
    if 'user_id' not in session:
        return jsonify([])
        
    conn = get_db()
    cursor = conn.cursor()
    
    if session.get('role') == 'admin':
        target_user_id = request.args.get('target_user_id')
        if not target_user_id:
            conn.close()
            return jsonify([])
        cursor.execute("SELECT id, user_id, room_user_id, nama_user, role, pesan, created_at FROM messages WHERE room_user_id = ? ORDER BY id ASC", (int(target_user_id),))
    else:
        cursor.execute("SELECT id, user_id, room_user_id, nama_user, role, pesan, created_at FROM messages WHERE room_user_id = ? ORDER BY id ASC", (session['user_id'],))
        
    rows = cursor.fetchall()
    conn.close()
    
    chat_data = [{
        'id': r['id'], 'user_id': r['user_id'], 'room_user_id': r['room_user_id'], 
        'nama_user': r['nama_user'], 'role': r['role'], 'pesan': r['pesan'], 
        'time': r['created_at'][11:16] if r['created_at'] else ''
    } for r in rows]
    return jsonify(chat_data)

@app.route('/api/chat/users')
def chat_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify([])
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.room_user_id, u.nama_lengkap, u.email, u.no_whatsapp,
               (SELECT pesan FROM messages WHERE room_user_id = m.room_user_id ORDER BY id DESC LIMIT 1) as last_msg,
               (SELECT created_at FROM messages WHERE room_user_id = m.room_user_id ORDER BY id DESC LIMIT 1) as last_time
        FROM messages m
        JOIN users u ON m.room_user_id = u.id
        WHERE m.room_user_id IS NOT NULL
        GROUP BY m.room_user_id
        ORDER BY last_time DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    user_list = [{
        'room_user_id': r['room_user_id'],
        'nama_lengkap': r['nama_lengkap'],
        'email': r['email'],
        'no_whatsapp': r['no_whatsapp'],
        'last_msg': r['last_msg'],
        'last_time': r['last_time'][11:16] if r['last_time'] else ''
    } for r in rows]
    return jsonify(user_list)

@app.route('/syarat_ketentuan')
def syarat_ketentuan():
    return render_template('syarat_ketentuan.html')

@app.route('/kebijakan_privasi')
def kebijakan_privasi():
    return render_template('kebijakan_privasi.html')

# --- ROUTE GENERATOR SEEDER DATA OTOMATIS ---
@app.route('/admin/generate-seed')
def admin_generate_seed():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Akses khusus administrator!', 'danger')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # 1. TEMPLATE DUMMY USERS TRAVELER
    dummy_users = [
        ('Nagisa Shiota', 'nagisa@opentrip.com', '081298765432'),
        ('Ferda Nur', 'ferda@opentrip.com', '085712345678'),
        ('Ahmad Firdaus', 'firdaus@opentrip.com', '081311223344'),
        ('Vina Aulia', 'vina@opentrip.com', '089677889900'),
        ('Azmi Al Fahriza', 'azmi@opentrip.com', '082155443322'),
        ('Dea Amellya', 'dea@opentrip.com', '083899001122')
    ]
    
    user_ids = []
    for nama, email, wa in dummy_users:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        u = cursor.fetchone()
        if u:
            user_ids.append(u['id'])
        else:
            pass_hash = generate_password_hash('user123')
            cursor.execute("INSERT INTO users (nama_lengkap, email, password, no_whatsapp, role) VALUES (?, ?, ?, ?, 'traveler')",
                           (nama, email, pass_hash, wa))
            user_ids.append(cursor.lastrowid)

    # 2. TEMPLATE DUMMY PAKET TRIP (10 VARIATIF)
    trips_template = [
        ('Exotic Labuan Bajo Phinisi', 'Labuan Bajo', 2500000, 10, '15/10/2026', 'Bandara Komodo (LBJ)', '3D2N', 'https://images.unsplash.com/photo-1516690561799-46d8f74892f1?w=800', 'Sailing Phinisi mengelilingi pulau Komodo & Padar.', 'Kapal Phinisi AC, Makan 3x, Alat Snorkeling, Guide HPI, Drone', 'Hari 1: Kelor - Kalong | Hari 2: Padar - Pink Beach - Manta Point | Hari 3: Kanawa - Drop LBJ', 'Bahari'),
        ('Magical Raja Ampat Wayag', 'Raja Ampat', 4800000, 6, '20/10/2026', 'Bandara DEO Sorong', '4D3N', 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800', 'Surga terumbu karang terbaik dunia di gugusan karst Wayag.', 'Speedboat VIP, Homestay Apung, Makan Seafood, Pin Konservasi', 'Hari 1: Sorong - Waisai | Hari 2: Wayag Karst - Shark Point | Hari 3: Piaynemo - Pasir Timbul', 'Bahari'),
        ('Golden Sunrise Bromo Express', 'Bromo, Malang', 850000, 12, '12/10/2026', 'Stasiun Malang Kota', '2D1N', 'https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=800', 'Berburu sunrise Bromo dan jelajah Pasir Berbisik naik Jeep 4x4.', 'Jeep 4x4, Homestay Bromo, Tiket Masuk TNNB, Guide Lokal', 'Hari 1: Penjemputan Malang - Check in Homestay | Hari 2: Sunrise Penanjakan - Kawah Bromo - Savana', 'Pegunungan'),
        ('Trekking Rinjani Peak 3726', 'Lombok', 1950000, 8, '05/11/2026', 'Bandara LOP / Mataram', '3D2N', 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800', 'Petualangan puncak Rinjani dan menginap di Danau Segara Anak.', 'Porter Alat & Tenda, Makan 3x/Hari, Tiket TNGR, Guide Gunung', 'Hari 1: Sembalun - Pos 3 - Plawangan Sembalun | Hari 2: Summit 3726 - Segara Anak | Hari 3: Senaru - Drop', 'Pegunungan'),
        ('Nusa Penida Island Hopping', 'Bali', 650000, 15, '18/10/2026', 'Pelabuhan Sanur Bali', '1D', 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800', 'Jelajah destinasi viral Kelingking Beach & Broken Beach Nusa Penida.', 'Fastboat PP Sanur, Mobil AC Penida, Makan Siang, Tiket Masuk', 'Hari 1: Sanur - Kelingking Beach - Broken Beach - Angel Billabong - Crystal Bay - Sanur', 'Island Hopping'),
        ('Derawan & Maratua Jellyfish', 'Berau, Kaltim', 3200000, 8, '22/11/2026', 'Bandara Kalimarau Berau', '4D3N', 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800', 'Berenang bersama ubur-ubur tanpa sengat di Kakaban & Maratua.', 'Speedboat Tour, Water Villa Derawan, Alat Snorkeling, Guide', 'Hari 1: Berau - Derawan | Hari 2: Maratua - Kakaban Lake | Hari 3: Sangalaki Pari Manta | Hari 4: Drop Berau', 'Bahari'),
        ('Dieng Culture Festival & Sikunir', 'Wonosobo', 950000, 14, '01/11/2026', 'Stasiun Purwokerto', '2D1N', 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800', 'Negeri di atas awan Dieng, Telaga Warna, dan Golden Sunrise Sikunir.', 'Elf Long AC, Homestay Dieng, Tiket Candi & Sikunir, Makan 3x', 'Hari 1: Purwokerto - Candi Arjuna - Telaga Warna | Hari 2: Sunrise Sikunir - Batu Ratapan - Return', 'Culture & Heritage'),
        ('Belitung Laskar Pelangi Tour', 'Belitung', 1450000, 10, '10/11/2026', 'Bandara Hanandjoeddin', '3D2N', 'https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=800', 'Jelajah batu granit raksasa Pulau Lengkuas dan SD Laskar Pelangi.', 'Boat Tradisional Jelajah Pulau, Hotel AC, Makan Seafood, Alat Snorkel', 'Hari 1: Pantai Tanjung Tinggi - SD Laskar Pelangi | Hari 2: Island Hopping Lengkuas | Hari 3: Mie Belitung', 'Island Hopping'),
        ('Ijen Blue Fire & Baluran', 'Banyuwangi', 890000, 12, '28/10/2026', 'Stasiun Banyuwangi Kota', '2D1N', 'https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800', 'Fenomena langka Api Biru (Blue Fire) Kawah Ijen & Afrika-nya Jawa Baluran.', 'Trooper 4x4 Ijen, Masker Gas Respirator, Tiket TN Ijen & Baluran, Hotel', 'Hari 1: Baluran Savana Bekol - Pantai Bama | Hari 2: 01.00 Trekking Ijen Blue Fire - Return', 'Pegunungan'),
        ('Toraja Cultural Heritage', 'Tana Toraja', 2800000, 6, '05/12/2026', 'Bandara Sultan Hasanuddin', '4D3N', 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800', 'Wisata sejarah & budaya unik rumah adat Tongkonan serta Lemo Kete Kesu.', 'Transport AC Makassar-Toraja, Hotel Bintang 3, Guide Budaya, Tiket', 'Hari 1: Makassar - Enrekang - Toraja | Hari 2: Kete Kesu - Lemo - Londa | Hari 3: Batutumonga | Hari 4: Drop', 'Culture & Heritage')
    ]

    trip_ids = []
    for t in trips_template:
        cursor.execute("SELECT id FROM trips WHERE judul_trip = ?", (t[0],))
        existing_t = cursor.fetchone()
        if existing_t:
            trip_ids.append(existing_t['id'])
        else:
            cursor.execute('''INSERT INTO trips 
                (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url, deskripsi, fasilitas, rundown, kategori)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', t)
            trip_ids.append(cursor.lastrowid)

    # 3. TEMPLATE DUMMY ARTIKEL WISATA (8 ARTIKEL)
    artikels_template = [
        ('10 Barang Wajib Bawa Saat Open Trip Laut & Island Hopping', 'Travel Guide', '01/10/2026', 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800', 'Persiapan barang bawaan sangat vital saat mengikuti Open Trip jelajah pulau. Pastikan membawa dry bag tahan air, sunscreen ramah terumbu karang (reef-safe) minimal SPF 50+, kacamata hitam UV protection, sandal gunung anti-slip, dan obat antimual perjalanan laut.', 'Tim Editorial OP Trip'),
        ('Tips Bebas Altitude Sickness / Hipoksia Saat Naik Gunung', 'Tips Wisata', '02/10/2026', 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800', 'Menghadapi ketinggian di atas 2.500 MDPL membutuhkan aklimatisasi tubuh yang baik. Minumlah air putih minimal 3 liter sehari, lakukan langkah jalan stabil tanpa terburu-buru, serta hindari tidur terlalu tinggi tanpa istirahat jeda.', 'Guide Gunung OP Trip'),
        ('Estimasi Panduan Budget Liburan Hemat ke Labuan Bajo 2026', 'Budgeting', '03/10/2026', 'https://images.unsplash.com/photo-1516690561799-46d8f74892f1?w=800', 'Sailing Komodo tidak selalu mahal. Dengan memilih sistem Open Trip dibanding Private Boat, kamu bisa menghemat budget hingga 60% dengan fasilitas mewah kapal Phinisi AC yang tetap sama.', 'Keuangan Traveler'),
        ('Etika Berfoto & Berinteraksi dengan Warga Lokal Toraja', 'Kuliner & Budaya', '04/10/2026', 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800', 'Menghormati adat istiadat setempat adalah aturan nomor satu saat berkunjung ke situs pemakaman batu Lemo atau Kete Kesu di Toraja. Selalu minta izin sebelum memotret dan kenakan pakaian sopan.', 'Tim Kebudayaan'),
        ('Rahasia Waktu Terbaik Berburu Blue Fire Kawah Ijen', 'Tips Wisata', '05/10/2026', 'https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800', 'Api biru alami Kawah Ijen hanya terlihat sempurna di kegelapan malam antara pukul 02.00 hingga 04.00 WIB. Pastikan kamu sudah siap melintasi rute pendakian dari Pos Paltuding jam 01.00 Dini Hari.', 'Rangga Pratama'),
        ('7 Kuliner Khas Belitung yang Wajib Dicoba Traveler', 'Kuliner & Budaya', '05/10/2026', 'https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=800', 'Selain keindahan pantai batu granit, Belitung menyimpan kelezatan wisata kuliner seperti Mie Belitung Atep berkuah udang kental, Kopi Kong Djie legendaris, serta Gangan Sup Ikan Kuning asam pedas.', 'Tim Kuliner'),
        ('Persiapan Fisik 2 Minggu Sebelum Trekking Puncak Rinjani', 'Travel Guide', '06/10/2026', 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800', 'Jalur Sembalun Rinjani terkenal dengan bukit penyesalan yang terjal. Lakukan latihan fisik kardio seperti jogging berkala, naik turun tangga, dan squat-jump setidaknya 14 hari sebelum hari H keberangkatan.', 'Tim Outdoor'),
        ('Mengapa Terumbu Karang Raja Ampat Disebut Amazon Lautan?', 'Travel Guide', '07/10/2026', 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800', 'Raja Ampat menampung lebih dari 75% seluruh spesies terumbu karang yang ada di bumi! Keanekaragaman hayati ini menjadikannya destinasi impian setiap diver dan penyelam di dunia.', 'Tim Konservasi')
    ]

    for a in artikels_template:
        cursor.execute("SELECT id FROM artikels WHERE judul = ?", (a[0],))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO artikels (judul, kategori, tanggal, gambar_url, isi_artikel, author) VALUES (?, ?, ?, ?, ?, ?)", a)

    # 4. TEMPLATE DUMMY TRANSAKSI PESANAN (BOOKINGS VARIATIF)
    # Dibuat dengan berbagai rentang tanggal (Hari ini, Minggu ini, Bulan ini) untuk grafik omset
    today_dt = datetime.now()
    dates_sample = [
        today_dt.strftime('%Y-%m-%d %H:%M:%S'), # Hari Ini
        (today_dt - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), # Kemarin
        (today_dt - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'), # Minggu Ini
        (today_dt - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'), # Minggu Ini
        (today_dt - timedelta(days=12)).strftime('%Y-%m-%d %H:%M:%S'), # Bulan Ini
        (today_dt - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S'), # Bulan Ini
        (today_dt - timedelta(days=45)).strftime('%Y-%m-%d %H:%M:%S')  # Tahun Ini
    ]

    bookings_sample = [
        (user_ids[0], trip_ids[0], 2, 5000000, 'lunas', 'Transfer BCA', dates_sample[0]),
        (user_ids[1], trip_ids[1], 1, 4800000, 'lunas', 'Transfer Mandiri', dates_sample[0]),
        (user_ids[2], trip_ids[2], 3, 2550000, 'pending', 'Transfer BNI', dates_sample[1]),
        (user_ids[3], trip_ids[3], 2, 3900000, 'lunas', 'Transfer BCA', dates_sample[2]),
        (user_ids[4], trip_ids[4], 4, 2600000, 'lunas', 'QRIS Mandiri', dates_sample[3]),
        (user_ids[5], trip_ids[5], 2, 6400000, 'pending', 'Transfer BCA', dates_sample[4]),
        (user_ids[0], trip_ids[6], 2, 1900000, 'lunas', 'Transfer BRI', dates_sample[5]),
        (user_ids[1], trip_ids[7], 1, 1450000, 'lunas', 'Transfer BCA', dates_sample[6]),
        (user_ids[2], trip_ids[8], 2, 1780000, 'ditolak', 'Transfer Bank', dates_sample[1]),
        (user_ids[3], trip_ids[9], 2, 5600000, 'lunas', 'Transfer BCA', dates_sample[4]),
    ]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    if cursor.fetchone()[0] < 5:
        for u_id, t_id, pax, total, st, met, dt in bookings_sample:
            cursor.execute('''
                INSERT INTO bookings (user_id, trip_id, jumlah_pax, total_harga, status_pembayaran, metode_pembayaran, created_at, catatan_pesanan)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Mohon infokan meeting point terupdate via WA ya kak')
            ''', (u_id, t_id, pax, total, st, met, dt))

    conn.commit()
    conn.close()

    flash('🎉 Berhasil me-load puluhan Template Otomatis untuk Paket Trip, Artikel, dan Transaksi!', 'success')
    return redirect(url_for('admin_dashboard', tab='rekap'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)