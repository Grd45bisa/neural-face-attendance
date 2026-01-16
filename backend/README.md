# Face Recognition Attendance System - Backend API

Backend API untuk sistem presensi siswa berbasis face recognition menggunakan Flask, MongoDB, dan JWT authentication.

## 🚀 Features

- **Authentication & Authorization**
  - JWT-based authentication (access + refresh tokens)
  - Password hashing dengan bcrypt
  - Role-based access control (student, teacher, admin)

- **Face Recognition**
  - Face registration dengan OpenCV DNN detector
  - Face verification menggunakan MobileNetV2 embeddings
  - Automatic attendance creation pada face verification

- **Attendance Management**
  - Manual dan face-based check-in/check-out
  - Attendance history dengan filtering
  - Statistics dan reporting
  - Admin approval system

- **User Management**
  - User profile management
  - Password change
  - Admin user management

## 📋 System Requirements

- Python 3.8+
- MongoDB 4.4+
- 4GB RAM minimum (8GB recommended untuk face recognition)
- Windows/Linux/MacOS

## 🛠️ Installation

### 1. Clone Repository

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup MongoDB

**Install MongoDB:**
- Download dari [MongoDB Download Center](https://www.mongodb.com/try/download/community)
- Install dan jalankan MongoDB service

**Verify MongoDB is running:**
```bash
# Windows
net start MongoDB

# Linux
sudo systemctl status mongod

# Mac
brew services start mongodb-community
```

**Test connection:**
```bash
mongosh
# atau
mongo
```

### 5. Configure Environment Variables

Copy `.env.example` ke `.env`:
```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` file:
```env
# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=tugas

# JWT (CHANGE THESE IN PRODUCTION!)
JWT_SECRET_KEY=your-super-secret-key-here
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key-here

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-flask-secret-key

# Face Recognition
FACE_DB_PATH=../data/embeddings.pkl
FACE_CONFIDENCE_THRESHOLD=0.7
```

### 6. Create Data Directory

```bash
mkdir -p ../data
```

## 🚀 Running the Server

### Development Mode

```bash
python app.py
```

Server akan berjalan di: `http://localhost:5000`

### Production Mode

```bash
# Set environment
set FLASK_ENV=production  # Windows
export FLASK_ENV=production  # Linux/Mac

# Run with gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## 📚 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Authentication Endpoints

#### 1. Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "password123",
  "name": "John Doe",
  "role": "student",
  "metadata": {
    "phone": "08123456789",
    "class": "12A",
    "student_id": "2024001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "user_id": "user_abc123",
      "email": "student@example.com",
      "name": "John Doe",
      "role": "student",
      "face_registered": false
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "password123"
}
```

#### 3. Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 4. Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### User Profile Endpoints

#### 1. Get Profile
```http
GET /api/user/profile
Authorization: Bearer <access_token>
```

#### 2. Update Profile
```http
PUT /api/user/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "John Updated",
  "metadata": {
    "phone": "08199999999"
  }
}
```

#### 3. Change Password
```http
PUT /api/user/password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "password123",
  "new_password": "newpassword456"
}
```

### Face Recognition Endpoints

#### 1. Register Face
```http
POST /api/face/register
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

photo: <file>
```

**Or with base64:**
```http
POST /api/face/register
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Face registered successfully",
  "data": {
    "user_id": "user_abc123",
    "photo_path": "user_abc123/xyz.jpg",
    "confidence": 0.98
  }
}
```

#### 2. Verify Face (Auto Check-in)
```http
POST /api/face/verify
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

photo: <file>
```

**Response:**
```json
{
  "success": true,
  "message": "Face verified successfully",
  "data": {
    "verified": true,
    "user_id": "user_abc123",
    "confidence": 0.92,
    "attendance": {
      "_id": "attendance_id",
      "user_id": "user_abc123",
      "timestamp": "2025-12-04T09:00:00",
      "type": "check-in",
      "method": "face",
      "confidence": 0.92,
      "status": "approved"
    }
  }
}
```

#### 3. Check Face Status
```http
GET /api/face/status/<user_id>
Authorization: Bearer <access_token>
```

### Attendance Endpoints

#### 1. Manual Check-in
```http
POST /api/attendance/check-in
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "location": "Room 101"
}
```

#### 2. Get Attendance History
```http
GET /api/attendance/history?page=1&per_page=20&start_date=2025-12-01&end_date=2025-12-31
Authorization: Bearer <access_token>
```

#### 3. Get Today's Attendance
```http
GET /api/attendance/today
Authorization: Bearer <access_token>
```

#### 4. Get Statistics
```http
GET /api/attendance/stats?start_date=2025-12-01&end_date=2025-12-31
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 45,
    "check_ins": 23,
    "check_outs": 22,
    "face_method": 40,
    "manual_method": 5,
    "approved": 43,
    "pending": 2,
    "rejected": 0
  }
}
```

### Admin Endpoints

#### 1. Get All Users
```http
GET /api/user/all?role=student&page=1&per_page=50
Authorization: Bearer <admin_access_token>
```

#### 2. Get All Attendance (Daily)
```http
GET /api/attendance/all?date=2025-12-04
Authorization: Bearer <admin_access_token>
```

#### 3. Verify Attendance
```http
PUT /api/attendance/<attendance_id>/verify
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "status": "approved"
}
```

## 🔒 Security

### Password Requirements
- Minimum 8 characters
- At least one letter
- At least one number

### JWT Tokens
- **Access Token**: Expires in 1 hour
- **Refresh Token**: Expires in 7 days
- Tokens are signed with HS256 algorithm

### File Upload
- Maximum file size: 5MB
- Allowed formats: JPG, PNG, JPEG
- Files are validated and sanitized

## 📁 Project Structure

```
backend/
├── app.py                  # Main Flask application
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore
│
├── routes/                # API routes
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── user.py           # User management endpoints
│   ├── face.py           # Face recognition endpoints
│   └── attendance.py     # Attendance endpoints
│
├── models/               # Database models
│   ├── __init__.py
│   ├── user.py          # User model
│   └── attendance.py    # Attendance model
│
├── middleware/          # Middleware
│   ├── __init__.py
│   └── auth_middleware.py  # JWT authentication
│
├── utils/              # Utility functions
│   ├── __init__.py
│   ├── response.py     # API response formatters
│   ├── validators.py   # Input validators
│   └── file_handler.py # File upload handlers
│
├── face_recognition/   # Face recognition modules
│   ├── __init__.py
│   ├── face_detector.py
│   ├── face_encoder.py
│   ├── face_recognizer.py
│   └── database_manager.py
│
└── uploads/           # Uploaded files
    ├── faces/        # Face registration photos
    └── attendance/   # Attendance verification photos
```

## 🐛 Troubleshooting

### MongoDB Connection Error
```
Failed to connect to MongoDB
```
**Solution:**
- Pastikan MongoDB service berjalan
- Check MongoDB URI di `.env` file
- Test connection: `mongosh` atau `mongo`

### Import Error: No module named 'cv2'
```
ModuleNotFoundError: No module named 'cv2'
```
**Solution:**
```bash
pip install opencv-python
```

### JWT Token Expired
```
Token has expired
```
**Solution:**
- Use refresh token untuk mendapatkan access token baru
- Call `/api/auth/refresh` endpoint

### Face Not Detected
```
No face detected in image
```
**Solution:**
- Pastikan foto jelas dan wajah terlihat
- Gunakan pencahayaan yang cukup
- Pastikan hanya ada 1 wajah dalam foto untuk registration

### File Too Large
```
File too large. Maximum size: 5MB
```
**Solution:**
- Compress image sebelum upload
- Resize image ke ukuran lebih kecil

## 🧪 Testing

### Test MongoDB Connection
```bash
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('Connected:', client.server_info())"
```

### Test API Endpoints

**Using curl:**
```bash
# Health check
curl http://localhost:5000/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"password123\",\"name\":\"Test User\"}"
```

**Using Postman:**
1. Import endpoints dari dokumentasi di atas
2. Set Authorization header: `Bearer <token>`
3. Test semua endpoints

## 📝 Development Notes

### Adding New Endpoints
1. Create route function di `routes/`
2. Add validation menggunakan `utils/validators.py`
3. Use response formatters dari `utils/response.py`
4. Register blueprint di `app.py`

### Database Schema Changes
1. Update model di `models/`
2. Add indexes di `_ensure_indexes()` method
3. Test dengan sample data

### Face Recognition Tuning
- Adjust `FACE_CONFIDENCE_THRESHOLD` di `.env`
- Modify detection parameters di `face_recognition/`

## 📄 License

This project is for educational purposes.

## 👥 Support

Untuk pertanyaan atau issues, silakan contact developer.

---

**Happy Coding! 🚀**
