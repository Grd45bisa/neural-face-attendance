# Attendance API - Business Logic Documentation

## Overview

Sistem presensi dengan business rules yang spesifik untuk kehadiran siswa.

## Business Rules

### 1. Check-in Rules
- **1x per hari**: User hanya bisa presensi 1 kali per hari
- **Waktu terlambat**: Check-in setelah jam **07:30 WIB** dianggap **LATE**
- **Minimum confidence**: Score minimal **0.6** (60%) untuk valid
- **Face registration required**: User harus sudah registrasi wajah

### 2. Status Types
- `present`: Check-in sebelum atau tepat jam 07:30 WIB
- `late`: Check-in setelah jam 07:30 WIB
- `absent`: Tidak check-in (auto-created by system)

### 3. Timezone
- **WIB (UTC+7)**: Semua waktu menggunakan timezone WIB
- Database menyimpan dalam UTC, tapi logic menggunakan WIB

## MongoDB Schemas

### users Collection
```javascript
{
  _id: ObjectId,
  user_id: String (unique, "user_abc123"),
  email: String (unique),
  password_hash: String (bcrypt),
  full_name: String,
  nis: String (Nomor Induk Siswa),
  class_name: String,
  phone: String,
  role: String ("student" | "teacher" | "admin"),
  is_face_registered: Boolean,
  face_photo_path: String,
  created_at: Date,
  updated_at: Date
}
```

### attendance Collection
```javascript
{
  _id: ObjectId,
  user_id: String (reference to users.user_id),
  date: String (YYYY-MM-DD),
  check_in_time: DateTime (UTC),
  photo_url: String,
  confidence_score: Float (0-1),
  status: String ("present" | "late" | "absent"),
  type: String ("check-in" | "absent"),
  method: String ("face" | "auto"),
  created_at: DateTime (UTC)
}
```

### face_embeddings Collection
```javascript
{
  _id: ObjectId,
  user_id: String (reference to users.user_id),
  embeddings: Array<Float> (1280 dimensions),
  registered_at: DateTime,
  photo_count: Number (3-10),
  verification_count: Number,
  last_verified: DateTime
}
```

## API Endpoints

### POST /api/attendance/checkin

Check-in dengan face verification.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request (File Upload):**
```
photo: File (JPG/PNG, max 5MB)
```

**Request (Base64):**
```json
{
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Check-in successful! Status: PRESENT",
  "data": {
    "_id": "attendance_id",
    "user_id": "user_abc123",
    "date": "2025-12-04",
    "check_in_time": "2025-12-04T00:15:23Z",
    "check_in_time_wib": "07:15:23",
    "photo_url": "uploads/attendance/user_abc123/photo.jpg",
    "confidence_score": 0.92,
    "status": "present",
    "type": "check-in",
    "method": "face"
  }
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "You have already checked in today"
}
```

**Error Cases:**
- `400` - User has not registered face
- `400` - Confidence score too low (< 0.6)
- `400` - Already checked in today
- `400` - No face detected
- `400` - Face does not match

---

### GET /api/attendance/today

Get today's attendance for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Today's attendance retrieved successfully",
  "data": {
    "_id": "attendance_id",
    "user_id": "user_abc123",
    "date": "2025-12-04",
    "check_in_time_wib": "07:15:23",
    "status": "present",
    "confidence_score": 0.92
  }
}
```

**Response (200) - No attendance:**
```json
{
  "success": true,
  "message": "No attendance record for today",
  "data": null
}
```

---

### GET /api/attendance/history

Get attendance history dengan pagination.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `user_id`: User ID (optional, default: current user)
- `month`: Month 1-12 (optional)
- `year`: Year (optional)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Example:**
```
GET /api/attendance/history?month=12&year=2024&page=1&per_page=20
```

**Response (200):**
```json
{
  "success": true,
  "message": "History retrieved successfully",
  "data": {
    "records": [
      {
        "_id": "attendance_id",
        "user_id": "user_abc123",
        "date": "2025-12-04",
        "check_in_time_wib": "2025-12-04 07:15:23",
        "status": "present",
        "confidence_score": 0.92
      }
    ],
    "total": 45,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  }
}
```

---

### GET /api/attendance/stats

Get attendance statistics.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `user_id`: User ID (optional, default: current user)

**Response (200):**
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_present": 35,
    "total_late": 8,
    "total_absent": 2,
    "total_days": 45,
    "attendance_percentage": 95.56,
    "streak": 7
  }
}
```

**Fields:**
- `total_present`: Jumlah hadir tepat waktu
- `total_late`: Jumlah terlambat
- `total_absent`: Jumlah tidak hadir
- `total_days`: Total hari
- `attendance_percentage`: Persentase kehadiran (present + late)
- `streak`: Consecutive days dengan attendance

---

### POST /api/attendance/admin/create-absent (Admin Only)

Create absent records untuk yang tidak presensi.

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "date": "2025-12-03"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Created 15 absent records",
  "data": {
    "absent_records_created": 15
  }
}
```

## Validation Rules

### Check-in Validation
1. ✅ User exists
2. ✅ User has registered face
3. ✅ Confidence score >= 0.6
4. ✅ No duplicate check-in today
5. ✅ Valid image format (JPG/PNG)
6. ✅ File size <= 5MB

### Date Validation
- Month: 1-12
- Year: 2000-2100
- Format: YYYY-MM-DD

## Timezone Handling

**WIB (UTC+7):**
- Semua business logic menggunakan WIB
- Late time: 07:30 WIB
- Date boundaries: 00:00 - 23:59 WIB

**UTC Storage:**
- Database menyimpan dalam UTC
- Conversion otomatis saat query dan response

**Example:**
```python
# User check-in at 07:15 WIB
check_in_time_wib = "2025-12-04 07:15:23 WIB"
# Stored in DB as UTC
check_in_time_utc = "2025-12-04 00:15:23 UTC"
# Status: "present" (before 07:30 WIB)
```

## Auto-Absent Records

**Cron Job (Daily):**
```bash
# Run at 23:59 every day
59 23 * * * curl -X POST http://localhost:5000/api/attendance/admin/create-absent \
  -H "Authorization: Bearer <admin_token>"
```

**Logic:**
1. Get all students with registered faces
2. Check if they have attendance for yesterday
3. If not, create absent record
4. Return count of created records

## Testing Examples

### 1. Check-in (Success)
```bash
curl -X POST http://localhost:5000/api/attendance/checkin \
  -H "Authorization: Bearer <token>" \
  -F "photo=@selfie.jpg"
```

### 2. Check-in (Duplicate)
```bash
# Second check-in on same day
curl -X POST http://localhost:5000/api/attendance/checkin \
  -H "Authorization: Bearer <token>" \
  -F "photo=@selfie.jpg"

# Response: "You have already checked in today"
```

### 3. Get Today's Attendance
```bash
curl http://localhost:5000/api/attendance/today \
  -H "Authorization: Bearer <token>"
```

### 4. Get History (December 2024)
```bash
curl "http://localhost:5000/api/attendance/history?month=12&year=2024&page=1" \
  -H "Authorization: Bearer <token>"
```

### 5. Get Statistics
```bash
curl http://localhost:5000/api/attendance/stats \
  -H "Authorization: Bearer <token>"
```

### 6. Create Absent Records (Admin)
```bash
curl -X POST http://localhost:5000/api/attendance/admin/create-absent \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-12-03"}'
```

## Error Handling

### Common Errors

**Face Not Registered:**
```json
{
  "success": false,
  "message": "User has not registered face. Please register face first."
}
```

**Low Confidence:**
```json
{
  "success": false,
  "message": "Confidence score too low (0.45). Minimum required: 0.6"
}
```

**Duplicate Check-in:**
```json
{
  "success": false,
  "message": "You have already checked in today"
}
```

**Invalid Date:**
```json
{
  "success": false,
  "message": "Invalid month. Must be between 1 and 12"
}
```

## Dependencies

Add to `requirements.txt`:
```
pytz==2023.3
```

Install:
```bash
pip install pytz
```

---

**Happy Coding! 🚀**
