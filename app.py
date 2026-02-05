from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import os
import json
import datetime
import random
import mysql.connector

app = Flask(__name__)
app.secret_key = 'kuncirahasiabigdata' 

# --- KONFIGURASI DATABASE ---
UPLOAD_FOLDER = 'static/uploads'
NOSQL_FILE = 'reports.json'      # Hanya untuk backup
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smartcity_db'
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- LOAD AI ---
print("Memuat AI...")
try:
    model = load_model('model_jalan.h5')
    print("AI Siap!")
except:
    model = None
    print("AI Gagal dimuat (Cek file .h5)")

# ==========================================
# 1. KONEKSI MYSQL
# ==========================================
def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error Koneksi MySQL: {err}")
        return None

# ==========================================
# 2. FUNGSI NOSQL (JSON) - HANYA UNTUK BACKUP
# ==========================================
def load_nosql_reports():
    if not os.path.exists(NOSQL_FILE): return []
    with open(NOSQL_FILE, 'r') as f:
        try: return json.load(f)
        except: return []

def save_report_nosql(data):
    reports = load_nosql_reports()
    reports.append(data)
    with open(NOSQL_FILE, 'w') as f: json.dump(reports, f, indent=4)

# --- AI & PREDIKSI ---
def predict_damage(image_path):
    img = load_img(image_path, target_size=(150, 150))
    x = img_to_array(img) / 255.0
    x = np.expand_dims(x, axis=0)
    pred = model.predict(x)[0]
    idx = np.argmax(pred)
    conf = float(round(np.max(pred) * 100, 1))
    labels = {0: "Normal", 1: "Rusak Berat", 2: "Rusak Ringan"}
    priority = 3 if idx == 1 else (2 if idx == 2 else 1)
    return labels.get(idx, "Unknown"), conf, int(priority)

# --- KOORDINAT (GPS) ---
def add_simulated_coordinates(reports):
    center_lat, center_long = -6.2088, 106.8456
    for r in reports:
        # Menangani lat/lng dari MySQL (Decimal) atau JSON
        lat = r.get('lat') or r.get('latitude')
        lng = r.get('lng') or r.get('longitude')
        
        if lat is None or lat == 0:
            r['lat'] = center_lat + random.uniform(-0.05, 0.05)
            r['lng'] = center_long + random.uniform(-0.05, 0.05)
        else:
            r['lat'] = float(lat)
            r['lng'] = float(lng)
    return reports

# ==========================================
# ROUTES
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def lapor():
    if request.method == 'POST':
        if 'file' not in request.files: return redirect(request.url)
        file = request.files['file']
        lokasi = request.form.get('lokasi', 'Tanpa Lokasi')
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')

        if file.filename != '':
            # Buat nama file unik
            filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Prediksi AI
            label, conf, p_score = predict_damage(filepath)
            
            # --- COBA SIMPAN KE MYSQL ---
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # QUERY INI HARUS COCOK 100% DENGAN NAMA KOLOM DI PHPMYADMIN
                    query = """
                        INSERT INTO reports 
                        (id, location_text, latitude, longitude, image_path, ai_label, ai_confidence, priority_score, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Pastikan lat/lng tidak error jika kosong
                    val_lat = float(lat) if lat else None
                    val_lng = float(lng) if lng else None
                    
                    val = (filename, lokasi, val_lat, val_lng, filepath, label, conf, p_score, 'Menunggu')
                    
                    cursor.execute(query, val)
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    # JIKA SUKSES
                    return render_template('index.html', success=True, label=label)
                    
            except mysql.connector.Error as err:
                # JIKA GAGAL: Tampilkan error di layar web
                print(f"ERROR DATABASE: {err}") # Cek terminal juga
                return f"<h1>GAGAL MENYIMPAN KE DATABASE!</h1><p>Error: {err}</p><p>Coba cek nama kolom di phpMyAdmin apakah sudah sesuai dengan: id, location_text, latitude, longitude, image_path, ai_label, ai_confidence, priority_score, status</p>"
            except Exception as e:
                return f"<h1>ERROR SYSTEM: {e}</h1>"

            # Backup JSON (Opsional)
            try:
                report_data = {
                    "id": filename, "waktu": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "lokasi": lokasi, "gambar": filepath, "hasil_ai": label,
                    "confidence": conf, "priority_score": p_score, "status": "Menunggu"
                }
                save_report_nosql(report_data)
            except:
                pass

    return render_template('index.html')

# --- ADMIN DASHBOARD (PERBAIKAN UTAMA DI SINI) ---
@app.route('/admin')
def admin_dashboard():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    reports = []
    teams = []
    
    # Nilai default jika database kosong/error
    total = 0
    berat = 0
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # 1. AMBIL DATA UNTUK TABEL (List Laporan)
        # Pastikan kolom 'reported_at' ada di database, atau gunakan 'created_at' sesuai tabel Baginda
        query_reports = """
            SELECT 
                id, 
                location_text as lokasi, 
                image_path as gambar, 
                ai_label as hasil_ai, 
                priority_score, 
                status, 
                reported_at as waktu, 
                ai_confidence as confidence,
                latitude as lat,
                longitude as lng
            FROM reports 
            ORDER BY priority_score DESC
        """
        cursor.execute(query_reports)
        reports = cursor.fetchall()
        
        # 2. AMBIL DATA TIM
        cursor.execute("SELECT * FROM teams")
        teams = cursor.fetchall()

        # --- PERBAIKAN UTAMA DI SINI (MENGHITUNG TOTAL & ALERT VIA SQL) ---
        
        # Hitung TOTAL semua laporan
        cursor.execute("SELECT COUNT(*) as jum FROM reports")
        res_total = cursor.fetchone()
        total = res_total['jum'] if res_total else 0
        
        # Hitung PENDING ALERTS (Rusak Berat & Belum Selesai)
        # Syarat: Priority=3 (Berat) DAN Status bukan 'Selesai'
        cursor.execute("""
            SELECT COUNT(*) as jum 
            FROM reports 
            WHERE priority_score = 3 AND status != 'Selesai'
        """)
        res_berat = cursor.fetchone()
        berat = res_berat['jum'] if res_berat else 0
        
        cursor.close()
        conn.close()
    
    # Tambahkan koordinat acak jika kosong (untuk peta)
    reports = add_simulated_coordinates(reports)
    
    return render_template('admin_dashboard.html', 
                           page='dashboard', reports=reports, teams=teams, total=total, berat=berat)

@app.route('/admin/map')
def map_view():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    reports = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Gunakan Alias juga di sini
        cursor.execute("""
            SELECT id, location_text as lokasi, image_path as gambar, ai_label as hasil_ai, 
                   latitude as lat, longitude as lng, priority_score 
            FROM reports
        """)
        reports = cursor.fetchall()
        conn.close()
        
    reports = add_simulated_coordinates(reports)
    return render_template('admin_map.html', page='map', reports=reports)

@app.route('/admin/reports')
def reports_view():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    reports = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Gunakan Alias
        cursor.execute("""
            SELECT id, location_text as lokasi, image_path as gambar, ai_label as hasil_ai, 
                   priority_score, status, created_at as waktu 
            FROM reports 
            ORDER BY priority_score DESC
        """)
        reports = cursor.fetchall()
        conn.close()
        
    return render_template('admin_reports.html', page='reports', reports=reports)

@app.route('/admin/teams', methods=['GET', 'POST'])
def teams_view():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if request.method == 'POST' and conn:
        team_id = request.form.get('team_id')
        new_status = request.form.get('status')
        cursor = conn.cursor()
        cursor.execute("UPDATE teams SET status = %s WHERE id = %s", (new_status, team_id))
        conn.commit()
        cursor.close()
        flash('Status Tim Berhasil Diupdate!', 'success')
    
    teams = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM teams")
        teams = cursor.fetchall()
        conn.close()
    
    return render_template('admin_teams.html', page='teams', teams=teams)

@app.route('/admin/settings')
def settings_view():
    if 'logged_in' not in session: return redirect(url_for('login'))
    return render_template('admin_settings.html', page='settings')

# --- AUTH ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = None
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
        
        if user:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Login Gagal (Cek User di MySQL)")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/action/<report_id>/<action>')
def report_action(report_id, action):
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    new_status = "Menunggu"
    if action == 'proses': new_status = "Sedang Dikerjakan"
    elif action == 'selesai': new_status = "Selesai"
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reports SET status = %s WHERE id = %s", (new_status, report_id))
        conn.commit()
        conn.close()
    
    return redirect(request.referrer) 

if __name__ == '__main__':
    app.run(debug=True)