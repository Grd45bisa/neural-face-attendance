# 📥 Panduan Instalasi & Penggunaan Neural Face Attendance

Panduan lengkap untuk menginstall dan menggunakan sistem face recognition attendance, mulai dari instalasi hingga testing real-time.

---

## 📋 Daftar Isi

1. [System Requirements](#-system-requirements)
2. [Instalasi Python Dependencies](#-instalasi-python-dependencies)
3. [Instalasi MongoDB](#-instalasi-mongodb)
4. [Setup Project](#-setup-project)
5. [Mode 1: CLI Real-Time Recognition](#-mode-1-cli-real-time-recognition)
6. [Mode 2: Web Application](#-mode-2-web-application)
7. [Troubleshooting](#-troubleshooting)

---

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10/11, Linux Ubuntu 20.04+, macOS 12+ |
| **Python** | 3.9 - 3.10 (Recommended: **3.10**) |
| **RAM** | 8 GB minimum |
| **Storage** | 5 GB free space |
| **Webcam** | USB Webcam atau built-in camera |
| **Node.js** | v18+ (untuk frontend) |
| **MongoDB** | v4.6+ |

### Untuk GPU Acceleration (Opsional tapi Direkomendasikan)

| GPU | Requirements |
|-----|--------------|
| **NVIDIA** | CUDA 11.8+, cuDNN 8.x, Driver 450+ |
| **AMD** | ROCm (Linux only) |

> ⚠️ **Catatan:** Tanpa GPU, sistem tetap berjalan di CPU tapi lebih lambat (15 FPS vs 30+ FPS).

---

## 📦 Instalasi Python Dependencies

### Step 1: Buat Virtual Environment

```bash
# Masuk ke folder project
cd neural-face-attendance

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Step 2: Install Dependencies Utama

Berikut adalah **semua dependencies yang dibutuhkan** untuk real-time face recognition:

```bash
# Core Dependencies (WAJIB)
pip install opencv-python==4.8.1.78      # Untuk camera & image processing
pip install numpy==1.24.3                 # Untuk numerical operations
pip install tensorflow==2.15.0            # Untuk deep learning (MobileNetV2)
pip install Pillow==10.1.0                # Untuk image handling

# Database & Storage
pip install pymongo==4.6.1                # Untuk MongoDB connection

# Backend API (jika pakai web app)
pip install Flask==3.0.0                  # Web framework
pip install Flask-CORS==4.0.0             # Cross-origin support
pip install PyJWT==2.8.0                  # JWT authentication
pip install bcrypt==4.1.2                 # Password hashing
pip install python-dotenv==1.0.0          # Environment variables
pip install pytz==2023.3                  # Timezone support
```

### Atau Install Semua Sekaligus

```bash
# Install dari requirements.txt root project
pip install -r requirements.txt

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 3: Verifikasi Instalasi

```bash
# Test OpenCV
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"

# Test TensorFlow
python -c "import tensorflow as tf; print(f'TensorFlow: {tf.__version__}')"

# Test GPU (jika ada)
python -c "import tensorflow as tf; print(f'GPU Available: {len(tf.config.list_physical_devices(\"GPU\")) > 0}')"
```

**Output yang benar:**
```
OpenCV: 4.8.1
TensorFlow: 2.15.0
GPU Available: True (atau False jika tidak ada GPU)
```

---

## 🍃 Instalasi MongoDB

MongoDB diperlukan untuk **web application** (untuk menyimpan data user dan attendance records).

### Windows

1. Download MongoDB Community Server dari: https://www.mongodb.com/try/download/community
2. Install dengan opsi default
3. MongoDB akan otomatis berjalan sebagai Windows Service

### Atau Pakai MongoDB Atlas (Cloud) 

Jika tidak ingin install MongoDB lokal:
1. Buat akun di https://www.mongodb.com/cloud/atlas
2. Buat cluster gratis
3. Copy connection string, contoh: `mongodb+srv://user:password@cluster.mongodb.net/`

### Verifikasi MongoDB

```bash
# Windows (CMD)
mongosh

# Di mongosh shell
> db.version()
```

---

## ⚙️ Setup Project

### Step 1: Clone Repository

```bash
git clone https://github.com/Grd45bisa/neural-face-attendance.git
cd neural-face-attendance
```

### Step 2: Download Model Files

Model akan **auto-download** saat pertama kali dijalankan, atau bisa manual:

```bash
python download_models.py
```

File yang akan didownload:
- `src/core/models/deploy.prototxt` (~28 KB)
- `src/core/models/res10_300x300_ssd_iter_140000.caffemodel` (~10 MB)

### Step 3: Buat Folder Data

```bash
mkdir data
```

---

## 🖥️ Mode 1: CLI Real-Time Recognition

Mode ini adalah cara **paling simple** untuk testing face recognition tanpa perlu setup backend/frontend.

### Quick Start

```bash
# Pastikan di folder project dan venv aktif
cd neural-face-attendance
venv\Scripts\activate  # Windows

# Masuk ke folder src
cd src

# Jalankan aplikasi
python main_app.py --help
```

### Langkah 1: Register Wajah Baru

```bash
# Register user baru dari webcam (ambil 5 foto)
python main_app.py register --name "Nama Kamu" --photos 5
```

**Apa yang terjadi:**
1. Webcam akan terbuka
2. Tekan **SPACE** untuk capture foto (5 kali)
3. Tekan **Q** untuk selesai
4. Wajah akan di-encode menggunakan MobileNetV2
5. Embedding disimpan ke `data/face_db.pkl`

### Langkah 2: Live Face Recognition

```bash
# Start real-time recognition
python main_app.py recognize
```

**Kontrol Keyboard:**

| Key | Function |
|-----|----------|
| `Q` / `ESC` | Keluar |
| `S` | Save screenshot |
| `P` | Pause/Resume |
| `R` | Register user baru (langsung dari sini) |
| `F` | Force re-recognition |
| `+` / `-` | Adjust similarity threshold |

**Output di layar:**
- Kotak hijau = Wajah dikenali (confidence tinggi)
- Kotak kuning = Wajah dikenali (confidence sedang)
- Kotak merah = Unknown / tidak dikenali
- FPS counter di pojok kiri atas

### Langkah 3: Test dari File Image

```bash
# Test recognition dari file gambar
python main_app.py test --image-path ../test_photos/foto_kamu.jpg --show

# Test multiple images dengan pattern
python main_app.py test --image-path "../test_photos/*.jpg" --save
```

### Langkah 4: Lihat Database User

```bash
# List semua user yang terdaftar
python main_app.py list-users --format table

# Output:
# User ID              Name                 Registered           Photos
# -----------------------------------------------------------------------
# user_20260116        Pahmi                2026-01-16           5
# user_20260115        Budi                 2026-01-15           3
```

### Langkah 5: Statistik Database

```bash
python main_app.py stats

# Output:
# ============================================================
# DATABASE STATISTICS
# ============================================================
# Total Users: 5
# Embedding Dimension: 1280
# Database Size: 125.45 KB
# Created: 2026-01-10
# Last Updated: 2026-01-16
# ============================================================
```

---

## 🌐 Mode 2: Web Application

Mode ini untuk pengalaman lengkap dengan UI web modern.

### Setup Backend

#### Step 1: Konfigurasi Environment

```bash
cd backend
copy .env.example .env
```

Edit file `.env`:

```env
# Flask Config
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# MongoDB (Local)
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=face_attendance

# Atau MongoDB Atlas (Cloud)
# MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/
# MONGO_DB_NAME=face_attendance

# CORS (untuk frontend)
CORS_ORIGINS=http://localhost:5173
```

#### Step 2: Jalankan Backend

```bash
# Windows
start_backend.bat

# Atau manual
cd backend
python app.py
```

**Output yang benar:**
```
============================================================
Face Recognition Attendance API
============================================================
Environment: development
Debug mode: True
MongoDB: mongodb://localhost:27017/face_attendance
Server: http://localhost:5000
============================================================
```

#### Step 3: Test Backend

Buka browser: http://localhost:5000

```json
{
    "name": "Face Recognition Attendance API",
    "version": "1.0.0",
    "status": "running",
    "endpoints": {
        "auth": "/api/auth",
        "user": "/api/user",
        "face": "/api/face",
        "attendance": "/api/attendance"
    }
}
```

### Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Jalankan development server
npm run dev
```

**Output:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Buka browser: http://localhost:5173

### Flow Penggunaan Web App

1. **Register Account** - Buat akun baru dengan email & password
2. **Login** - Masuk ke sistem
3. **Register Face** - Upload atau capture foto wajah via webcam
4. **Attendance** - Check-in/out dengan verifikasi wajah real-time
5. **Dashboard** - Lihat history presensi

---

## 🔧 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'cv2'`

```bash
pip install opencv-python==4.8.1.78
```

### Error: `Cannot open camera`

1. Pastikan webcam tidak dipakai aplikasi lain
2. Coba ganti camera ID:
   ```bash
   python main_app.py recognize --camera-id 1
   ```

### Error: `TensorFlow tidak detect GPU`

1. Install CUDA 11.8 dan cuDNN 8.x
2. Restart terminal setelah install
3. Verifikasi:
   ```bash
   python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
   ```

### Error: `MongoDB connection failed`

1. Pastikan MongoDB service berjalan
2. Cek connection string di `.env`
3. Windows: Buka Services → MongoDB Server → Start

### Error: `ImportError: DLL load failed`

Ini biasanya masalah Visual C++ Redistributable:
```bash
# Download dan install:
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### FPS Rendah (< 10 FPS)

1. Kurangi resolusi camera:
   ```python
   # Di live_tracker.py, ubah resolution
   camera = CameraHandler(camera_id=0, resolution=(640, 480))
   ```

2. Skip lebih banyak frames:
   ```python
   config = {'process_every_n_frames': 4}  # dari 2 jadi 4
   ```

---

## 📊 Performance Tips

### Untuk Real-Time Recognition yang Smooth:

1. **Gunakan GPU** - 2-3x lebih cepat dari CPU
2. **Resolusi 720p** - Balance antara akurasi dan speed
3. **Lighting yang baik** - Akurasi detection bisa turun 10% di low light
4. **Jarak wajah optimal** - 0.5m - 2m dari kamera

### Expected Performance:

| Hardware | FPS | Latency |
|----------|-----|---------|
| Intel i5 (CPU) | 15-20 | ~65ms |
| Intel i7 (CPU) | 20-25 | ~45ms |
| NVIDIA GTX 1650 | 30+ | ~33ms |
| NVIDIA RTX 3060 | 45+ | ~22ms |

---

## ✅ Checklist Sebelum Running

- [ ] Python 3.10 terinstall
- [ ] Virtual environment aktif
- [ ] OpenCV terinstall dan bisa import
- [ ] TensorFlow terinstall dan bisa import
- [ ] MongoDB berjalan (untuk web app)
- [ ] Webcam tersedia dan tidak dipakai app lain
- [ ] Folder `data/` sudah dibuat

---

**🎉 Selesai! Sistem siap digunakan.**

Jika ada pertanyaan, buka issue di GitHub atau hubungi tim pengembang.
