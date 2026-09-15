from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import time

app = Flask(__name__)
app.secret_key = 'opentrip_flask_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def init_db():
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nama_lengkap TEXT, email TEXT UNIQUE, password TEXT, no_whatsapp TEXT, role TEXT DEFAULT 'traveler'
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT, judul_trip TEXT, destinasi TEXT, harga_per_pax INTEGER, sisa_kuota INTEGER, tanggal_berangkat TEXT, meeting_point TEXT, durasi TEXT, gambar_url TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, trip_id INTEGER, jumlah_pax INTEGER, total_harga INTEGER, bukti_transfer TEXT, status_pembayaran TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute("SELECT * FROM users WHERE email = 'admin@opentrip.com'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (nama_lengkap, email, password, no_whatsapp, role) VALUES (?, ?, ?, ?, ?)",
                       ('Admin OP Trip', 'admin@opentrip.com', admin_pass, '081234567890', 'admin'))
        
    cursor.execute("SELECT COUNT(*) FROM trips")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO trips (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Sailing Exotic Labuan Bajo', 'Labuan Bajo', 2500000, 8, '25 Oktober 2026', 'Bandara Komodo (LBJ)', '3D2N', 'https://images.unsplash.com/photo-1516690561799-46d8f74892f1?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'))
        cursor.execute("INSERT INTO trips (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Exploring Paradise Raja Ampat', 'Raja Ampat', 4800000, 4, '10 November 2026', 'Pelabuhan Sorong', '4D3N', 'https://images.unsplash.com/photo-1544644181-1484b3fdfc62?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'))
        cursor.execute("INSERT INTO trips (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ('Private Sunrise Mount Bromo', 'Bromo', 1200000, 12, '05 Oktober 2026', 'Stasiun Malang', '2D1N', 'https://images.unsplash.com/photo-1609830530737-01ef06d88b0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'))

    conn.commit()
    conn.close()

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect('opentrip.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (request.form['email'],))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], request.form['password']):
            session['user_id'], session['nama_lengkap'], session['role'] = user[0], user[1], user[5]
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Email atau kata sandi tidak sesuai.', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pass = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('opentrip.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (nama_lengkap, email, password, no_whatsapp) VALUES (?, ?, ?, ?)",
                           (request.form['nama_lengkap'], request.form['email'], hashed_pass, request.form['no_whatsapp']))
            conn.commit()
            flash('Akun berhasil dibuat! Silakan login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email sudah terdaftar.', 'danger')
        finally:
            conn.close()
    return render_template('auth/register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        conn = sqlite3.connect('opentrip.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (request.form['email'],))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", (generate_password_hash(request.form['password']), request.form['email']))
            conn.commit()
            flash('Kata sandi diperbarui! Silakan login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email tidak ditemukan.', 'danger')
        conn.close()
    return render_template('auth/forgot.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN DASHBOARD ---
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
        
    search, destinasi_filter = request.args.get('search', ''), request.args.get('destinasi', '')
    query, params = "SELECT * FROM trips WHERE 1=1", []
    
    if search:
        query += " AND (judul_trip LIKE ? OR destinasi LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if destinasi_filter:
        query += " AND destinasi LIKE ?"
        params.append(f"%{destinasi_filter}%")
        
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    cursor.execute(query + " ORDER BY id DESC", params)
    trips = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', trips=trips, search=search, destinasi_filter=destinasi_filter)

# --- ROUTE ADMIN DASHBOARD & KELOLA DATA ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Akses khusus admin!', 'danger')
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    
    # Ambil Statistik
    cursor.execute("SELECT COUNT(*) FROM trips")
    total_trips = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_harga) FROM bookings WHERE status_pembayaran = 'lunas'")
    total_omset = cursor.fetchone()[0] or 0
    
    # Ambil Data Trips
    cursor.execute("SELECT * FROM trips ORDER BY id DESC")
    trips = cursor.fetchall()
    
    # Ambil Data Bookings + Join User & Trip
    cursor.execute('''
        SELECT bookings.id, users.nama_lengkap, users.no_whatsapp, trips.judul_trip, 
               bookings.jumlah_pax, bookings.total_harga, bookings.bukti_transfer, 
               bookings.status_pembayaran, bookings.created_at
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        JOIN trips ON bookings.trip_id = trips.id
        ORDER BY bookings.id DESC
    ''')
    bookings = cursor.fetchall()
    
    conn.close()
    return render_template('admin/dashboard.html', total_trips=total_trips, total_bookings=total_bookings, total_omset=total_omset, trips=trips, bookings=bookings)

# --- ROUTE TAMBAH TRIP BARU (ADMIN) ---
@app.route('/admin/add-trip', methods=['POST'])
def admin_add_trip():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    judul = request.form['judul_trip']
    destinasi = request.form['destinasi']
    harga = int(request.form['harga_per_pax'])
    kuota = int(request.form['sisa_kuota'])
    tanggal = request.form['tanggal_berangkat']
    mepo = request.form['meeting_point']
    durasi = request.form['durasi']
    gambar = request.form['gambar_url'] or 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trips (judul_trip, destinasi, harga_per_pax, sisa_kuota, tanggal_berangkat, meeting_point, durasi, gambar_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (judul, destinasi, harga, kuota, tanggal, mepo, durasi, gambar))
    conn.commit()
    conn.close()
    
    flash('Paket Open Trip berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- ROUTE UPDATE STATUS BAYAR (ADMIN) ---
@app.route('/admin/update-booking/<int:booking_id>/<string:status>')
def admin_update_booking(booking_id, status):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status_pembayaran = ? WHERE id = ?", (status, booking_id))
    conn.commit()
    conn.close()
    
    flash(f'Status pemesanan berhasil diubah jadi {status.upper()}!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- DETAIL TRIP ---
@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
        
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    conn.close()
    
    if not trip: return redirect(url_for('dashboard'))
    
    rundown = [
        {"hari": "Hari 1", "judul": "Penjemputan & Eksplorasi Awal", "desc": "Penjemputan peserta di Meeting Point, perkenalan grup, makan siang bersama, dan mengunjungi destinasi pertama untuk menikmati Sunset."},
        {"hari": "Hari 2", "judul": "Full Day Tour & Hopping Island", "desc": "Bangun pagi, sarapan, lalu full day aktivitas utama (Snorkeling/Trekking). Termasuk makan siang eksklusif di lokasi wisata."},
        {"hari": "Hari 3", "judul": "Beli Oleh-oleh & Kepulangan", "desc": "Sarapan di penginapan, check-out, mampir ke pusat suvenir lokal khas daerah, dan pengantaran kembali ke Meeting Point. Sayonara!"}
    ]
        
    return render_template('trip_detail.html', trip=trip, rundown=rundown)

# --- ARTIKEL ---
@app.route('/artikel/<int:artikel_id>')
def artikel_detail(artikel_id):
    if 'user_id' not in session: return redirect(url_for('login'))
        
    artikels = {
        1: {"id": 1, "judul": "5 Barang Wajib Saat Open Trip Island Hopping", "kategori": "Travel Guide", "tanggal": "15 Sep 2026", "gambar": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80", "isi": "Persiapan barang bawaan sangat vital saat mengikuti Open Trip jelajah pulau. Pastikan kamu membawa dry bag anti air, pelindung matahari (sunscreen SPF 50+), obat mabuk laut, sepatu/sandal khusus air, dan powerbank berkapasitas besar."},
        2: {"id": 2, "judul": "Waktu Terbaik Mengunjungi Labuan Bajo", "kategori": "Destinasi", "tanggal": "10 Sep 2026", "gambar": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80", "isi": "Musim terbaik untuk mengarungi perairan Labuan Bajo adalah antara bulan April hingga November. Pada periode ini ombak cenderung tenang, langit cerah, dan rumput di Pulau Padar tampak berwarna hijau keemasan yang sangat estetik."},
        3: {"id": 3, "judul": "Tips Hemat Backpacker ke Raja Ampat", "kategori": "Budgeting", "tanggal": "05 Sep 2026", "gambar": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80", "isi": "Raja Ampat tidak selalu menguras kantong. Caranya: pesan tiket penerbangan jauh hari, pilih sistem gabung grup (Open Trip) untuk menekan biaya sewa speedboat yang mahal, serta menginap di homestay lokal milik warga setempat."},
        4: {"id": 4, "judul": "Rekomendasi Kuliner Seafood di Bali", "kategori": "Kuliner", "tanggal": "01 Sep 2026", "gambar": "https://images.unsplash.com/photo-1534080564583-6be75777b70a?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80", "isi": "Liburan ke pantai belum lengkap tanpa mencicipi hidangan laut. Kawasan Jimbaran menjadi spot terbaik untuk menikmati ikan bakar segar sembari melihat matahari terbenam. Jangan lupa cicipi sate lilit khas Bali!"},
        5: {"id": 5, "judul": "Persiapan Fisik Mendaki Gunung Bromo", "kategori": "Travel Guide", "tanggal": "28 Agu 2026", "gambar": "https://images.unsplash.com/photo-1609830530737-01ef06d88b0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80", "isi": "Meskipun Bromo tergolong gunung yang ramah pemula dan bisa diakses dengan Jeep, suhu dingin yang menusuk tulang dan jalur berpasir menuntut fisik yang prima. Jangan lupa bawa jaket tebal dan masker anti debu."}
    }
    
    artikel = artikels.get(artikel_id, artikels[1])
    return render_template('artikel_detail.html', artikel=artikel, semua_artikel=artikels)

# --- CHECKOUT ROUTE ---
@app.route('/checkout/<int:trip_id>', methods=['GET', 'POST'])
def checkout(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
        
    conn = sqlite3.connect('opentrip.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        jumlah_pax = int(request.form['jumlah_pax'])
        cursor.execute("SELECT harga_per_pax, sisa_kuota FROM trips WHERE id = ?", (trip_id,))
        trip_data = cursor.fetchone()
        
        if not trip_data or jumlah_pax > trip_data[1]:
            flash('Jumlah pesanan melebihi sisa kuota!', 'danger')
            conn.close()
            return redirect(url_for('checkout', trip_id=trip_id))
            
        file = request.files.get('bukti_transfer')
        filename = f"{int(time.time())}_{secure_filename(file.filename)}" if file and file.filename else ''
        if filename: file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        cursor.execute("INSERT INTO bookings (user_id, trip_id, jumlah_pax, total_harga, bukti_transfer, status_pembayaran) VALUES (?, ?, ?, ?, ?, 'pending')",
                       (session['user_id'], trip_id, jumlah_pax, jumlah_pax * trip_data[0], filename))
        cursor.execute("UPDATE trips SET sisa_kuota = ? WHERE id = ?", (trip_data[1] - jumlah_pax, trip_id))
        conn.commit()
        conn.close()
        return render_template('checkout.html', berhasil=True)
        
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    conn.close()
    return render_template('checkout.html', trip=trip, berhasil=False)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    app.run(debug=True, port=8000)