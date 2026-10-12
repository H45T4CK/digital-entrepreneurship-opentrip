# 🗺️ OP TRIP.ID — Open Trip Management & Online Booking System

![OP TRIP.ID Banner](https://images.unsplash.com/photo-1555400038-63f5ba517a47?auto=format&fit=crop&w=1200&q=80)

**OP TRIP.ID** adalah platform sistem informasi pemesanan (*booking*) dan manajemen operasional *Open Trip* berbasis web. Aplikasi ini dibangun untuk memudahkan para *traveler* menjelajahi berbagai destinasi wisata Nusantara (bahari, pegunungan, *island hopping*, budaya) sekaligus membantu pihak penyedia tur (*tour operator*) dalam mengelola katalog trip, verifikasi transaksi pembayaran, penerbitan *E-Ticket Boarding Pass*, pencetakan *manifest* peserta, hingga rekapitulasi laporan pendapatan finansial secara *real-time*.

---

## 📋 Daftar Isi

1. [Fitur Utama Aplikasi](#-fitur-utama-aplikasi)
2. [Teknologi & Stack](#-teknologi--stack)
3. [Arsitektur & Alur Kerja Sistem](#-arsitektur--alur-kerja-sistem)
4. [Skema Database (SQLite3)](#-skema-database-sqlite3)
5. [Panduan Instalasi & Pengoperasian Lokal](#-panduan-instalasi--pengoperasian-lokal)
6. [Kredensial Akun & Pengujian (Demo)](#-kredensial-akun--pengujian-demo)
7. [Dokumentasi Rute & API Endpoints](#-dokumentasi-rute--api-endpoints)
8. [Struktur Direktori Proyek](#-struktur-direktori-proyek)
9. [Lisensi & Penutup](#-lisensi--penutup)

---

## 🚀 Fitur Utama Aplikasi

### 👨‍🚀 1. Sisi Traveler (Pengguna / Guest)
* **Katalog & Eksplorasi Trip Modern:**
  * Pencarian langsung berdasarkan kata kunci nama trip, destinasi, atau deskripsi.
  * Filter kategori spesifik: *Bahari*, *Pegunungan*, dan *Island Hopping*.
  * Pengurutan (*sorting*) berdasarkan harga terendah, harga tertinggi, paket terbaru, serta kuota paling terbatas.
  * Pilihan cepat *Destinasi Populer* (Labuan Bajo, Bromo, Raja Ampat, Bali, dll.).
* **Detail Trip Komprehensif:**
  * Informasi jadwal keberangkatan, titik kumpul (*meeting point*), durasi, dan sisa kuota.
  * Breakdown rincian fasilitas termasuk (*Included*) dan tidak termasuk (*Excluded*).
  * Jadwal harian perjalanan (*Itinerary*) bertahap.
  * Modul Ulasan & Rating bintang 1–5 dari peserta terverifikasi.
* **Proses Checkout & Pembayaran Fleksibel:**
  * Kalkulasi dinamis harga total sesuai jumlah peserta (*pax*).
  * Pilihan rekening transfer bank nasional (BCA, Mandiri, BRI, BNI, BTN, CIMB Niaga).
  * Integrasi template visual **QRIS Standar Nasional MPM** (*Merchant Presented Mode*) untuk transaksi e-Wallet (GoPay, OVO, DANA, ShopeePay, LinkAja) & M-Banking.
  * Unggah bukti transfer/resi pembayaran dengan fitur *Pratinjau Gambar Langsung* (*Receipt Live Preview*).
* **Riwayat Pesanan & E-Document:**
  * Pemantauan status transaksi (*Lunas & Terkonfirmasi*, *Menunggu Verifikasi Admin*, atau *Ditolak*).
  * **Boarding Pass E-Ticket:** Tampilan tiket perjalanan siap cetak yang dilengkapi *QR Code Verification* & Barcode `Code 128`.
  * **E-Invoice Resmi:** Lembar invoice penagihan resmi PT Jelajah Petualang Nusantara dengan opsi cetak PDF presisi 1 halaman A4.
* **Live Chat Customer Service:**
  * Layanan obrolan interaktif dengan efek suara (*sound alert*) saat pesan terkirim/diterima.
  * Opsi pertanyaan cepat (*Quick Question Chips*) dan pintasan emoji.
* **Pusat Informasi & Legalitas:**
  * Artikel tips & panduan wisata (*Travel Guide*, *Budgeting*, *Kuliner & Budaya*).
  * Halaman Syarat & Ketentuan serta Kebijakan Privasi.

### ⚡ 2. Sisi Administrator (Pengelola Tur)
* **Dashboard Analytics & Finansial:**
  * Rekapitulasi omset dan total pesanan yang terfilter berdasarkan periode: **Hari Ini**, **7 Hari Terakhir (Minggu Ini)**, **Bulan Ini**, dan **Tahun Ini**.
  * Kartu indikator performa: Total Trip, Total Pesanan, Total Traveler, dan Total Artikel.
* **Manajemen Paket Open Trip (CRUD):**
  * Penambahan paket trip baru beserta unggah foto utama atau URL gambar Unsplash.
  * Penyuntingan rincian harga, sisa kuota, tanggal keberangkatan, meeting point, fasilitas, dan itinerary.
  * Penghapusan paket trip.
* **Manajemen Artikel Wisata (CRUD):**
  * Penerbitan panduan dan artikel edukasi traveler.
* **Verifikasi & Status Pembayaran:**
  * Peninjauan bukti transfer pengguna.
  * Perubahan status pesanan secara instan menjadi `lunas`, `pending`, atau `ditolak`.
* **Manifest Peserta Trip (Trip Passenger List):**
  * Generasi daftar nama peserta, nomor WhatsApp, email, dan catatan khusus khusus untuk trip terdaftar yang statusnya telah **LUNAS**.
* **Export Data Laporan:**
  * **Export CSV / Excel:** Unduh rekapitulasi data transaksi dan omset berformat `.csv` (UTF-8) sesuai periode yang dipilih.
  * **Export PDF Laporan:** Halaman laporan rekapitulasi finansial yang siap dicetak ke PDF.
* **Auto-Seeder Template Data (1-Click Generator):**
  * Fitur sekali klik di admin untuk mengisi database otomatis dengan 6 akun traveler dummy, 10 paket trip populer Indonesia, 8 artikel wisata, serta 10 variasi sampel transaksi.
* **Manajemen Pengguna & Peran:**
  * Pengubahan peran akun pengguna (*Traveler* ↔ *Admin*) serta penghapusan akun.

---

## 🛠️ Teknologi & Stack

### Backend
* **Python 3.10+**
* **Flask Web Framework** (Routing, Session Management, Template Rendering, JSON API)
* **Werkzeug** (Keamanan `generate_password_hash` / `check_password_hash` dengan algoritma PBKDF2:SHA256, secure filename upload)
* **SQLite3** (Database relasional tertanam dengan modul `sqlite3.Row` factory)

### Frontend
* **HTML5 & Jinja2 Template Engine**
* **Tailwind CSS (via CDN)** dengan kustomisasi *Glassmorphism UI* dan skema warna *Dark Mode Ambient Glow*.
* **Google Fonts:** *Plus Jakarta Sans* (Tipografi Utama) & *Libre Barcode 128* (Efek Barcode E-Ticket).
* **Vanilla JavaScript (ES6+):**
  * Async/Await Fetch API untuk *Live Chat Realtime*.
  * Web Audio API (`AudioContext`) untuk efek suara notifikasi *Live Chat*.
  * DOM Manipulation untuk perhitungan harga checkout dinamis, copy-to-clipboard nomor rekening, dan preview gambar resi.

---

## 📐 Arsitektur & Alur Kerja Sistem

```
                                  ┌───────────────────────────┐
                                  │   Traveler (Guest/User)   │
                                  └─────────────┬─────────────┘
                                                │
          ┌─────────────────────────────────────┼─────────────────────────────────────┐
          │                                     │                                     │
          ▼                                     ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐                  ┌──────────────────┐
│  Katalog & Filter│                  │ Checkout & Bayar │                  │ Live Chat CS API │
│   Paket Trip     │                  │ (Resi/QRIS/Bank) │                  │ (Long-Polling)   │
└─────────┬────────┘                  └─────────┬────────┘                  └─────────┬────────┘
          │                                     │                                     │
          └──────────────────┬──────────────────┘                                     │
                             ▼                                                        │
                   ┌──────────────────┐                                               │
                   │ Database SQLite3 │ ◄─────────────────────────────────────────────┘
                   └─────────┬────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │ Admin Dashboard    │
                  └──────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Verifikasi Resi │ │ Manifest Trip   │ │ Export Laporan  │
│ (Lunas/Ditolak) │ │ (Cetak Peserta) │ │ (CSV & PDF)     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🗄️ Skema Database (SQLite3)

Database disimpan pada file `opentrip.db` yang diinisialisasi secara otomatis saat aplikasi pertama kali dijalankan melalui fungsi `init_db()`.

### 1. Tabel `users`
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Identifier unik (Auto Increment) |
| `nama_lengkap` | TEXT NOT NULL | Nama pengguna |
| `email` | TEXT UNIQUE NOT NULL | Email login |
| `password` | TEXT NOT NULL | Password terenkripsi (Hash) |
| `no_whatsapp` | TEXT | Nomor WhatsApp |
| `role` | TEXT DEFAULT 'traveler' | Peran akun (`traveler` / `admin`) |
| `created_at` | TIMESTAMP | Waktu pembuatan akun |

### 2. Tabel `trips`
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Identifier unik trip |
| `judul_trip` | TEXT NOT NULL | Nama/Judul paket trip |
| `destinasi` | TEXT NOT NULL | Lokasi destinasi (misal: Labuan Bajo) |
| `harga_per_pax` | INTEGER NOT NULL | Harga per orang dalam Rupiah |
| `sisa_kuota` | INTEGER NOT NULL | Sisa kuota peserta yang tersedia |
| `tanggal_berangkat` | TEXT NOT NULL | Format tanggal (DD/MM/YYYY) |
| `meeting_point` | TEXT NOT NULL | Lokasi titik kumpul penjemputan |
| `durasi` | TEXT NOT NULL | Durasi paket (misal: 3D2N, 1D) |
| `gambar_url` | TEXT | Nama file upload atau URL Unsplash |
| `deskripsi` | TEXT | Penjelasan lengkap trip |
| `fasilitas` | TEXT | Rincian fasilitas |
| `rundown` | TEXT | Jadwal acara/itinerary |
| `kategori` | TEXT DEFAULT 'Bahari' | Kategori (`Bahari`, `Pegunungan`, `Island Hopping`) |

### 3. Tabel `bookings`
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | ID Booking Ununik |
| `user_id` | INTEGER NOT NULL | Foreign Key `users(id)` |
| `trip_id` | INTEGER NOT NULL | Foreign Key `trips(id)` |
| `jumlah_pax` | INTEGER NOT NULL | Jumlah peserta dipesan |
| `total_harga` | INTEGER NOT NULL | Total harga (pax * harga_per_pax) |
| `bukti_transfer` | TEXT | Nama file gambar resi yang diunggah |
| `status_pembayaran` | TEXT DEFAULT 'pending' | Status (`pending`, `lunas`, `ditolak`) |
| `metode_pembayaran` | TEXT | Nama bank/QRIS yang dipilih |
| `catatan_pesanan` | TEXT | Catatan opsional dari pemesan |
| `created_at` | TIMESTAMP | Waktu transaksi dibuat |

### 4. Tabel `artikels`
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | ID Artikel |
| `judul` | TEXT NOT NULL | Judul artikel panduan |
| `kategori` | TEXT NOT NULL | Kategori artikel |
| `tanggal` | TEXT NOT NULL | Tanggal publikasi |
| `gambar_url` | TEXT | Gambar header artikel |
| `isi_artikel` | TEXT | Konten lengkap artikel |
| `author` | TEXT | Nama penulis / Tim Editorial |

### 5. Tabel `reviews`
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | ID Ulasan |
| `trip_id` | INTEGER NOT NULL | Foreign Key `trips(id)` |
| `nama_user` | TEXT NOT NULL | Nama pemberi ulasan |
| `rating` | INTEGER DEFAULT 5 | Rating bintang (1–5) |
| `komentar` | TEXT | Isian ulasan pengguna |
| `created_at` | TIMESTAMP | Waktu ulasan dikirim |

### 6. Tabel `messages`
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | ID Pesan Chat |
| `user_id` | INTEGER NOT NULL | ID pengirim pesan |
| `room_user_id` | INTEGER | ID traveler pemilik ruang percakapan |
| `nama_user` | TEXT | Nama pengirim |
| `role` | TEXT | Peran pengirim (`admin` / `traveler`) |
| `pesan` | TEXT | Isi teks percakapan |
| `is_read` | INTEGER DEFAULT 0 | Penanda dibaca (`0` = Belum, `1` = Sudah) |
| `created_at` | TIMESTAMP | Waktu pengiriman pesan |

---

## 💻 Panduan Instalasi & Pengoperasian Lokal

Ikuti langkah-langkah di bawah ini untuk menjalankan proyek secara lokal di komputer kamu:

### 1. Prasyarat Sistem
* **Python** versi `3.10` atau lebih baru.
* **Git** (versi terbaru).
* Web Browser modern (Google Chrome, Mozilla Firefox, Microsoft Edge, atau Safari).

### 2. Clone Repository
Buka Terminal / Command Prompt / Git Bash, lalu jalankan:
```bash
git clone https://github.com/H45T4CK/optrip.git
cd optrip
```

### 3. Buat dan Aktifkan Virtual Environment
Sangat disarankan menggunakan *Virtual Environment* agar dependensi terisolasi dengan rapi.

* **Pada Windows (PowerShell / Command Prompt):**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```

* **Pada macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Instal Dependensi
Instal modul Python utama yang diperlukan:
```bash
pip install flask werkzeug
```

### 5. Jalankan Aplikasi Flask
Jalankan file utama `app_2.py`:
```bash
python app_2.py
```

Setelah berhasil dijalankan, terminal akan menampilkan output seperti ini:
```text
 * Serving Flask app 'app_2'
 * Debug mode: on
 * Running on http://127.0.0.1:8000
```

Buka peramban (browser) kamu dan akses alamat:
👉 **`http://localhost:8000`** atau **`http://127.0.0.1:8000`**

---

## 🔐 Kredensial Akun & Pengujian (Demo)

Sistem telah dilengkapi akun default dan seeder data dummy untuk kemudahan pengujian fitur.

### 1. Akun Admin Utama
* **Email:** `admin@opentrip.com`
* **Password:** `admin123`
* **Hak Akses:** Kelola Trip, Kelola Artikel, Konfirmasi Pembayaran, Manifest Peserta, Export CSV/PDF, dan Auto-Seed.

### 2. Akun Traveler Dummy (Hasil Auto-Seed)
Kamu dapat mengklik tombol **`⚡ Auto-Seed Template`** pada Header Panel Admin atau membuka URL `http://localhost:8000/admin/generate-seed` saat login sebagai admin. Akun traveler dummy yang dibuat:

| Nama Traveler | Email Login | Password | Nomor WhatsApp |
| :--- | :--- | :--- | :--- |
| Nagisa Shiota | `nagisa@opentrip.com` | `user123` | 081298765432 |
| Ferda Nur | `ferda@opentrip.com` | `user123` | 085712345678 |
| Ahmad Firdaus | `firdaus@opentrip.com` | `user123` | 081311223344 |
| Vina Aulia | `vina@opentrip.com` | `user123` | 089677889900 |
| Azmi Al Fahriza | `azmi@opentrip.com` | `user123` | 082155443322 |
| Dea Amellya | `dea@opentrip.com` | `user123` | 083899001122 |

---

## 🛣️ Dokumentasi Rute & API Endpoints

### 🔓 Rute Publik & Auth
| Metode HTTP | Endpoint | Deskripsi / Fungsi |
| :---: | :--- | :--- |
| `GET` | `/` atau `/dashboard` | Menampilkan katalog paket trip, filter kategori, pencarian, dan artikel |
| `GET`, `POST` | `/login` | Otentikasi masuk pengguna |
| `GET`, `POST` | `/register` | Pendaftaran akun traveler baru |
| `GET`, `POST` | `/forgot-password` | Pemulihan kata sandi dengan kode OTP demo |
| `GET` | `/logout` | Mengakhiri sesi login pengguna |
| `GET`, `POST` | `/trip/<trip_id>` | Menampilkan detail lengkap trip, itinerary, dan mengirim ulasan |
| `GET` | `/artikel/<artikel_id>` | Menampilkan konten lengkap artikel panduan wisata |
| `GET` | `/syarat_ketentuan` | Halaman dokumen Syarat & Ketentuan legal |
| `GET` | `/kebijakan_privasi` | Halaman dokumen Kebijakan Privasi |

### 🔒 Rute Terproteksi Traveler (User)
| Metode HTTP | Endpoint | Deskripsi / Fungsi |
| :---: | :--- | :--- |
| `GET`, `POST` | `/checkout/<trip_id>` | Form reservasi, pemilih pax, metode pembayaran, dan upload resi |
| `GET` | `/riwayat` | Menampilkan daftar riwayat pesanan user dan status verifikasinya |
| `GET` | `/invoice/<booking_id>` | Menampilkan E-Ticket Boarding Pass dan E-Invoice resmi siap cetak |

### ⚡ Rute Terproteksi Administrator
| Metode HTTP | Endpoint | Deskripsi / Fungsi |
| :---: | :--- | :--- |
| `GET` | `/admin` | Panel utama admin (Rekap Finansial, Daftar Trip, Artikel, Booking, Users) |
| `POST` | `/admin/add-trip` | Menambahkan paket open trip baru |
| `POST` | `/admin/edit-trip/<trip_id>` | Memperbarui data paket open trip |
| `GET` | `/admin/delete-trip/<trip_id>` | Menghapus paket open trip |
| `POST` | `/admin/add-artikel` | Menerbitkan artikel wisata baru |
| `POST` | `/admin/edit-artikel/<id>` | Memperbarui konten artikel |
| `GET` | `/admin/delete-artikel/<id>` | Menghapus artikel wisata |
| `GET` | `/admin/update-booking/<id>/<status>` | Mengubah status transaksi (`lunas`/`pending`/`ditolak`) |
| `GET` | `/admin/manifest/<trip_id>` | Menampilkan dan mencetak manifest daftar peserta lunas |
| `GET` | `/admin/user/toggle-role/<user_id>` | Mengubah peran akun (`traveler` ↔ `admin`) |
| `GET` | `/admin/user/delete/<user_id>` | Menghapus data akun pengguna |
| `GET` | `/admin/export/excel` | Mengunduh rekapitulasi data pesanan berformat CSV/Excel |
| `GET` | `/admin/export/pdf` | Menampilkan halaman laporan keuangan berformat PDF siap cetak |
| `GET` | `/admin/generate-seed` | Menjalankan pemuatan otomatis data sampel dummy |

### 💬 API Live Chat Async (JSON)
| Metode HTTP | Endpoint | Deskripsi / Fungsi |
| :---: | :--- | :--- |
| `POST` | `/api/chat/send` | Mengirim pesan percakapan baru (Payload JSON: `pesan`, `target_user_id`) |
| `GET` | `/api/chat/list` | Mengambil riwayat percakapan pengguna/room saat ini |
| `GET` | `/api/chat/users` | Mengambil daftar percakapan aktif dari seluruh traveler (Khusus Admin) |

---

## 📁 Struktur Direktori Proyek

```text
optrip/
├── app_2.py                    # Server Flask Backend, Database Init, & Controllers
├── opentrip.db                 # Database SQLite3 (Otomatis terbuat saat run)
├── README.md                   # Dokumentasi resmi proyek (File ini)
│
├── static/                     # Assets Statis
│   ├── logo.png                # Brand Logo OP TRIP.ID
│   └── uploads/                # Directory Penyimpanan Gambar Trip, Artikel & Resi Transfer
│
└── templates/                  # Jinja2 HTML Templates
    ├── admin/                  # Template Khusus Administrator
    │   ├── admin_dashboard.html# Dashboard Finansial, Manajemen CRUD & Status
    │   ├── export_pdf.html     # Layout Cetak Laporan Keuangan PDF
    │   └── manifest.html       # Layout Cetak Manifest Peserta Tur
    │
    ├── auth/                   # Template Otentikasi
    │   ├── login.html          # Halaman Masuk
    │   ├── register.html       # Halaman Pendaftaran
    │   └── forgot.html         # Halaman Reset Password OTP
    │
    ├── user_dashboard_2.html   # Homepage & Katalog Trip Utama
    ├── trip_detail.html        # Detail Trip, Fasilitas, Rundown & Ulasan
    ├── checkout.html           # Formulir Reservasi, Bank & QRIS MPM
    ├── riwayat.html            # Riwayat Pesanan & Status Traveler
    ├── invoice.html            # E-Ticket Boarding Pass & E-Invoice Cetak
    ├── chat_widget_2.html      # Widget Floating Live Chat Customer Service
    ├── syarat_ketentuan.html   # Halaman Dokumen Syarat & Ketentuan
    └── kebijakan_privasi.html  # Halaman Dokumen Kebijakan Privasi
```

---

## 📄 Lisensi & Penutup

Aplikasi **OP TRIP.ID** dikembangkan di bawah naungan **PT Jelajah Petualang Nusantara** sebagai solusi platform reservasi wisata terintegrasi. Bebas digunakan dan dikembangkan kembali untuk keperluan akademik, pembelajaran, maupun komersial.

> **Dikeluarkan oleh:** Tim Pengembang OP TRIP.ID  
> **Operational Manager:** Prajoko Subidodo  
> **Customer Support:** `admin@opentrip.com`