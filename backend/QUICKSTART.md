# Quick Start Guide

## 🚀 Cara Cepat Memulai Backend

### Windows

1. **Buka Command Prompt di folder backend**
   ```cmd
   cd backend
   ```

2. **Jalankan setup script**
   ```cmd
   setup.bat
   ```

3. **Edit file .env**
   - Buka `.env` dengan text editor
   - Ubah JWT secret keys (PENTING!)
   - Sesuaikan MongoDB URI jika perlu

4. **Install & Start MongoDB**
   - Download: https://www.mongodb.com/try/download/community
   - Install dan jalankan service:
     ```cmd
     net start MongoDB
     ```

5. **Jalankan server**
   ```cmd
   venv\Scripts\activate
   python app.py
   ```

6. **Test API**
   - Buka browser: http://localhost:5000
   - Health check: http://localhost:5000/health

### Linux/Mac

1. **Buka terminal di folder backend**
   ```bash
   cd backend
   ```

2. **Jalankan setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Edit file .env**
   ```bash
   nano .env  # atau editor favorit Anda
   ```

4. **Install & Start MongoDB**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mongodb
   sudo systemctl start mongod
   
   # Mac
   brew install mongodb-community
   brew services start mongodb-community
   ```

5. **Jalankan server**
   ```bash
   source venv/bin/activate
   python app.py
   ```

## 📝 Test API dengan curl

### 1. Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"student@example.com\",\"password\":\"password123\",\"name\":\"Test Student\"}"
```

### 2. Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"student@example.com\",\"password\":\"password123\"}"
```

Simpan `access_token` dari response!

### 3. Get Profile
```bash
curl http://localhost:5000/api/user/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Register Face
```bash
curl -X POST http://localhost:5000/api/face/register \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "photo=@path/to/your/photo.jpg"
```

### 5. Verify Face (Auto Check-in)
```bash
curl -X POST http://localhost:5000/api/face/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "photo=@path/to/your/photo.jpg"
```

## 🔧 Troubleshooting

### MongoDB Connection Error
```
Failed to connect to MongoDB
```
**Solusi:**
- Pastikan MongoDB service berjalan
- Check dengan: `mongosh` atau `mongo`
- Periksa MONGO_URI di file `.env`

### Import Error
```
ModuleNotFoundError: No module named 'flask'
```
**Solusi:**
```bash
# Pastikan virtual environment aktif
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install ulang dependencies
pip install -r requirements.txt
```

### Port Already in Use
```
Address already in use
```
**Solusi:**
```bash
# Windows - cari process di port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

## 📚 Dokumentasi Lengkap

Lihat [`README.md`](README.md) untuk:
- Dokumentasi API lengkap
- Semua endpoints dengan contoh
- Troubleshooting detail
- Production deployment guide

## 🎯 Next Steps

1. ✅ Setup backend (sudah selesai!)
2. 🔄 Test semua endpoints
3. 🎨 Buat frontend (React/Vue/Angular)
4. 🚀 Deploy ke production

## 💡 Tips

- Gunakan Postman untuk test API lebih mudah
- Import collection dari dokumentasi
- Enable debug mode untuk development
- Ganti semua secret keys untuk production!

---

**Selamat mencoba! 🎉**
