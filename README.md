#  Smart City: RoadGuard AI & Monitoring System

**RoadGuard AI** adalah platform *Smart City* berbasis web yang dirancang untuk memfasilitasi pelaporan kerusakan jalan oleh masyarakat secara *real-time*. Sistem ini mengintegrasikan **Kecerdasan Buatan (Deep Learning)** untuk memverifikasi dan mengklasifikasikan tingkat kerusakan jalan secara otomatis, serta menyediakan **Dashboard Admin** yang komprehensif untuk pemantauan geospasial dan manajemen tim lapangan.

##  Fitur Unggulan

###  Sisi Publik (Warga)
* **AI-Powered Reporting:** Pengguna mengunggah foto jalan rusak, dan sistem AI (TensorFlow/Keras) otomatis mendeteksi apakah kondisinya *Normal*, *Rusak Ringan*, atau *Rusak Berat*.
* **Geotagging Otomatis:** Mengambil koordinat GPS pengguna secara presisi atau memungkinkan pemilihan lokasi manual via peta interaktif (Leaflet.js).
* **Mode Gelap/Terang:** Antarmuka responsif dengan dukungan *theme switching* untuk kenyamanan visual.

###  Sisi Admin (Pemerintah/Dinas)
* **Dashboard Analitik:** Visualisasi statistik total laporan, tren kerusakan, dan peringatan dini (*Early Warning System*) untuk kerusakan kritis.
* **Peta Sebaran (Live Map):** Memantau titik-titik kerusakan jalan dalam tampilan peta visual dengan indikator warna berdasarkan tingkat keparahan.
* **Manajemen Tim Lapangan:** Memantau status ketersediaan tim (Available, Busy, Maintenance) untuk penugasan perbaikan yang efisien.
* **Sistem Tiket:** Mengelola status laporan dari "Menunggu" -> "Sedang Dikerjakan" -> "Selesai".
* **Export Data:** Fitur unduh rekapitulasi laporan ke format CSV.

---

##  Teknologi yang Digunakan

* **Bahasa Pemrograman:** Python 3.9+
* **Framework Web:** Flask (Jinja2 Template)
* **Machine Learning:** TensorFlow, Keras, NumPy
* **Database:** MySQL
* **Frontend:** Bootstrap 5, Leaflet.js (Maps), FontAwesome
* **Penyimpanan:** Local Storage (Uploads) & JSON Backup

---

##  Persiapan Instalasi

Sebelum menjalankan aplikasi, pastikan Anda telah menginstal:
1.  **Python** (versi 3.8 ke atas)
2.  **MySQL Server** (XAMPP/WAMP atau native MySQL)
3.  **Git**

### 1. Clone Repositori
```bash
git clone [https://github.com/username-anda/roadguard-ai.git](https://github.com/username-anda/roadguard-ai.git)
cd roadguard-ai
```

### 2. Setup Virtual Environment (Disarankan)

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instal Dependensi
```bash
pip install -r requirements.txt
```

**Catatan:** Jika file requirements.txt belum ada, instal manual library berikut:
```bash
pip install flask tensorflow numpy pillow mysql-connector-python
```

### 4. Konfigurasi Database

Buat database baru di MySQL bernama smartcity_db, lalu jalankan query SQL berikut untuk membuat tabel yang dibutuhkan:
```bash
CREATE DATABASE smartcity_db;
USE smartcity_db;

-- Tabel Laporan
CREATE TABLE reports (
    id VARCHAR(255) PRIMARY KEY,
    location_text VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    image_path TEXT,
    ai_label VARCHAR(50),
    ai_confidence FLOAT,
    priority_score INT,
    status VARCHAR(50) DEFAULT 'Menunggu',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Tim Lapangan
CREATE TABLE teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    contact VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Available'
);

-- Tabel Admin
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(255)
);

-- Data Dummy
INSERT INTO users (username, password) VALUES ('admin', 'admin123');
INSERT INTO teams (name, contact, status) VALUES 
('Tim Alpha', '0812-3333-4444', 'Available'),
('Tim Bravo', '0812-5555-6666', 'Busy'),
('Tim Charlie', '0812-7777-8888', 'Maintenance');
```

Sesuaikan konfigurasi database di file app.py jika username/password MySQL Anda berbeda:
```bash
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # Ganti sesuai user MySQL Anda
    'password': '',      # Ganti sesuai password Anda
    'database': 'smartcity_db'
}
```

### 5. Setup Model AI

Aplikasi ini membutuhkan file model model_jalan.h5.

1.  Unduh file model dari menu Releases di repositori ini.

2.  Letakkan file model_jalan.h5 di folder utama proyek (sejajar dengan app.py).

---

##  Cara Menjalankan

Jalankan perintah berikut di terminal:
```bash
python app.py
```

Akses aplikasi melalui browser:

* Halaman Publik (Lapor): http://127.0.0.1:5000/

* Dashboard Admin: http://127.0.0.1:5000/admin

  *   **Username** : admin

  *   **Password** : admin123

---

##  Struktur Folder (PENTING)

Agar aplikasi Flask berjalan dengan benar, pastikan Anda menyusun file-file yang Anda unduh ke dalam struktur folder berikut di komputer Anda. Jangan biarkan semua file menumpuk di satu folder luar.
```bash
roadguard-ai/
│
├── static/
│   └── uploads/             # (Buat manual) Tempat foto laporan tersimpan
│
├── templates/               # (Buat manual) Pindahkan semua file HTML ke sini
│   ├── admin_dashboard.html
│   ├── admin_map.html
│   ├── admin_reports.html
│   ├── admin_settings.html
│   ├── admin_teams.html
│   ├── base.html
│   ├── index.html
│   ├── lapor.html           # (Versi alternatif/lama)
│   └── login.html
│
├── app.py                   # File utama Python (tetap di luar)
├── model_jalan.h5           # Model AI (tetap di luar)
├── .gitignore
└── README.md
```

Penjelasan:

1. app.py dan model_jalan.h5 harus berada di folder paling luar (root).

2. Semua file berekstensi .html WAJIB dimasukkan ke dalam folder baru bernama templates.

3. Folder static/uploads akan dibuat otomatis oleh aplikasi jika belum ada, tetapi baiknya Anda menyiapkannya.

---

##  Keamanan & Privasi
Proyek ini dibuat untuk tujuan edukasi dan purwarupa Smart City. Hindari penggunaan data sensitif atau password asli pada konfigurasi database saat diunggah ke repositori publik. Pastikan file .env (jika ada) sudah dimasukkan ke dalam .gitignore.

---
<p align="center">
Dibuat oleh <b>Atma</b>, 
Mahasiswa Universitas Amikom Yogyakarta - Proyek Big Data & AI
</p>
