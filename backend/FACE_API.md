# Face Recognition API - Complete Documentation

## Overview

API untuk face recognition dengan MongoDB storage. Mendukung registrasi multi-foto (3-10 foto) untuk akurasi lebih tinggi.

## MongoDB Schema

### Collection: `face_embeddings`

```javascript
{
  _id: ObjectId,
  user_id: String (unique, reference ke users),
  embeddings: Array<Float> (1280 dimensi dari MobileNetV2),
  registered_at: Date,
  photo_count: Number (3-10),
  last_verified: Date,
  verification_count: Number
}
```

**Indexes:**
- `user_id`: Unique index untuk fast lookup

## API Endpoints

### 1. Register Face (Multi-Photo)

**Endpoint:** `POST /api/face/register`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request (File Upload):**
```
photos: File[] (3-10 foto wajah)
```

**Request (Base64):**
```json
{
  "photos_base64": [
    "data:image/jpeg;base64,/9j/4AAQ...",
    "data:image/jpeg;base64,/9j/4AAQ...",
    "data:image/jpeg;base64,/9j/4AAQ..."
  ]
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Face registered successfully",
  "data": {
    "user_id": "user_abc123",
    "photo_count": 5,
    "message": "Face registered successfully with 5 photos"
  }
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "Minimum 3 photos required for registration"
}
```

**Error Cases:**
- `400` - Minimum 3 photos required
- `400` - Maximum 10 photos allowed
- `400` - User already has face registered
- `400` - No face detected in photo
- `400` - Multiple faces detected
- `400` - Invalid image format
- `400` - File too large (max 5MB)

---

### 2. Verify Face

**Endpoint:** `POST /api/face/verify`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request (File Upload):**
```
photo: File (1 foto untuk verifikasi)
```

**Request (Base64):**
```json
{
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Face verified successfully",
  "data": {
    "verified": true,
    "user_id": "user_abc123",
    "confidence": 0.92,
    "message": "Face verified",
    "attendance": {
      "_id": "attendance_id",
      "user_id": "user_abc123",
      "timestamp": "2025-12-04T10:00:00",
      "type": "check-in",
      "method": "face",
      "confidence": 0.92,
      "status": "approved"
    }
  }
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "Face does not match (confidence: 0.45)",
  "errors": {
    "confidence": 0.45
  }
}
```

**Error Cases:**
- `400` - User face not registered
- `400` - No face detected in photo
- `400` - Multiple faces detected
- `400` - Face does not match (low confidence)
- `400` - Failed to preprocess face

---

### 3. Recognize Face (Identify User)

**Endpoint:** `POST /api/face/recognize`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:**
```
photo: File
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Face recognized successfully",
  "data": {
    "user_id": "user_abc123",
    "user_name": "John Doe",
    "confidence": 0.89,
    "message": "Face recognized as user user_abc123"
  }
}
```

**Response Error (404):**
```json
{
  "success": false,
  "message": "No match found (best confidence: 0.55)",
  "errors": {
    "confidence": 0.55
  }
}
```

---

### 4. Get Face Status

**Endpoint:** `GET /api/face/status`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "data": {
    "user_id": "user_abc123",
    "face_registered": true,
    "photo_count": 5,
    "registered_at": "2025-12-04T09:00:00",
    "verification_count": 15
  }
}
```

---

### 5. Delete Face Registration

**Endpoint:** `DELETE /api/face/delete`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Face registration deleted successfully",
  "data": null
}
```

---

### 6. Get Statistics (Admin Only)

**Endpoint:** `GET /api/face/stats`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_registered": 150,
    "avg_photos_per_user": 5.2,
    "total_verifications": 3420
  }
}
```

---

## Testing Examples

### Using curl

#### 1. Register Face (Multi-Photo)
```bash
curl -X POST http://localhost:5000/api/face/register \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg" \
  -F "photos=@photo3.jpg" \
  -F "photos=@photo4.jpg" \
  -F "photos=@photo5.jpg"
```

#### 2. Verify Face
```bash
curl -X POST http://localhost:5000/api/face/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "photo=@selfie.jpg"
```

#### 3. Recognize Face
```bash
curl -X POST http://localhost:5000/api/face/recognize \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "photo=@unknown_person.jpg"
```

#### 4. Get Status
```bash
curl http://localhost:5000/api/face/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 5. Delete Registration
```bash
curl -X DELETE http://localhost:5000/api/face/delete \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using Python

```python
import requests

# Login first
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'student@example.com',
    'password': 'password123'
})
token = login_response.json()['data']['access_token']

# Register face with multiple photos
files = [
    ('photos', open('photo1.jpg', 'rb')),
    ('photos', open('photo2.jpg', 'rb')),
    ('photos', open('photo3.jpg', 'rb')),
    ('photos', open('photo4.jpg', 'rb')),
    ('photos', open('photo5.jpg', 'rb'))
]

register_response = requests.post(
    'http://localhost:5000/api/face/register',
    headers={'Authorization': f'Bearer {token}'},
    files=files
)

print(register_response.json())

# Verify face
with open('selfie.jpg', 'rb') as f:
    verify_response = requests.post(
        'http://localhost:5000/api/face/verify',
        headers={'Authorization': f'Bearer {token}'},
        files={'photo': f}
    )

print(verify_response.json())
```

### Using JavaScript (Fetch)

```javascript
// Register face with multiple photos
const formData = new FormData();
formData.append('photos', photo1File);
formData.append('photos', photo2File);
formData.append('photos', photo3File);
formData.append('photos', photo4File);
formData.append('photos', photo5File);

const registerResponse = await fetch('http://localhost:5000/api/face/register', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const registerData = await registerResponse.json();
console.log(registerData);

// Verify face
const verifyFormData = new FormData();
verifyFormData.append('photo', selfieFile);

const verifyResponse = await fetch('http://localhost:5000/api/face/verify', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: verifyFormData
});

const verifyData = await verifyResponse.json();
console.log(verifyData);
```

---

## Best Practices

### Photo Requirements for Registration

1. **Quantity:** 5-7 foto recommended (minimum 3, maximum 10)
2. **Quality:** 
   - Resolusi minimal 640x480
   - Pencahayaan yang baik
   - Wajah jelas terlihat
3. **Variety:**
   - Berbagai sudut (frontal, slight left, slight right)
   - Berbagai ekspresi (normal, senyum)
   - Berbagai kondisi pencahayaan
4. **Consistency:**
   - Hanya 1 wajah per foto
   - Background yang tidak terlalu ramai
   - Tidak menggunakan kacamata hitam atau masker

### Confidence Threshold

- **Default:** 0.7 (70%)
- **Recommended:**
  - High security: 0.8-0.9
  - Normal: 0.7
  - Relaxed: 0.6

Adjust di `.env`:
```env
FACE_CONFIDENCE_THRESHOLD=0.7
```

### Error Handling

Selalu handle error cases:

```javascript
try {
  const response = await fetch('/api/face/verify', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const data = await response.json();
  
  if (!data.success) {
    // Handle error
    if (response.status === 400) {
      alert(data.message); // "Face does not match"
    } else if (response.status === 404) {
      alert('User face not registered');
    }
  } else {
    // Success
    console.log('Verified!', data.data.confidence);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

---

## Architecture

### Flow Diagram

```
Client Upload Photos
       ↓
API Endpoint (/api/face/register)
       ↓
FaceRecognitionService.register_user_face()
       ↓
For each photo:
  - FaceDetector.detect_faces()
  - FacePreprocessor.preprocess_face()
  - FaceEncoder.encode_face()
       ↓
Average all embeddings
       ↓
FaceEmbedding.register_face()
       ↓
Save to MongoDB (face_embeddings collection)
       ↓
Update User.face_registered = true
       ↓
Return success
```

### Components

1. **FaceRecognitionService** (`face_service.py`)
   - Wrapper class
   - Integrates existing face recognition code
   - Handles MongoDB storage

2. **FaceEmbedding Model** (`models/face_embedding.py`)
   - MongoDB CRUD operations
   - Embedding storage & retrieval

3. **Face Routes** (`routes/face.py`)
   - API endpoints
   - Request validation
   - Error handling

4. **Existing Face Recognition**
   - `FaceDetector` - OpenCV DNN
   - `FacePreprocessor` - Alignment & normalization
   - `FaceEncoder` - MobileNetV2 embeddings
   - `FaceMatcher` - Cosine similarity

---

## Troubleshooting

### "Minimum 3 photos required"
- Upload at least 3 photos
- Make sure all files are valid images

### "No face detected in photo"
- Ensure face is clearly visible
- Check lighting
- Face should be frontal or near-frontal

### "Multiple faces detected"
- Use photos with only 1 person
- Crop photo to show only target face

### "User already has face registered"
- Delete existing registration first: `DELETE /api/face/delete`
- Or use different user account

### "Face does not match"
- Confidence too low
- Try better quality photo
- Ensure good lighting
- Re-register with more varied photos

---

**Happy Coding! 🚀**
