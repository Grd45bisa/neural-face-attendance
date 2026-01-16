# Face Attendance System - Frontend

Modern React.js frontend untuk sistem presensi siswa berbasis face recognition dengan design flat dan clean.

## 🎨 Design

- **Color Palette**: Flat design tanpa gradient
  - Primary: #2563EB (Blue)
  - Secondary: #10B981 (Green)
  - Background: #FFFFFF (White)
  - Text: #1F2937 (Dark Gray)

- **UI Framework**: Tailwind CSS
- **Icons**: Lucide React
- **Font**: Inter (Google Fonts)

## 🚀 Features

- ✅ User authentication (Login/Register)
- ✅ Face registration dengan multi-photo capture (5-10 foto)
- ✅ Face verification untuk attendance
- ✅ Real-time camera integration
- ✅ Dashboard dengan statistics
- ✅ Attendance history
- ✅ Admin dashboard
- ✅ Responsive design (mobile-first)
- ✅ Toast notifications
- ✅ Protected routes
- ✅ Auto token refresh

## 📋 Prerequisites

- Node.js 16+ dan npm
- Backend API running di http://localhost:5000

## 🛠️ Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Frontend akan berjalan di: `http://localhost:3000`

## 📁 Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.jsx           # Halaman login
│   │   ├── Register.jsx        # Halaman register
│   │   ├── RegisterFace.jsx    # Registrasi wajah (multi-photo)
│   │   ├── Attendance.jsx      # Mark attendance
│   │   ├── Dashboard.jsx       # Dashboard siswa
│   │   └── Admin.jsx           # Admin dashboard
│   │
│   ├── components/
│   │   ├── Navbar.jsx          # Navigation bar
│   │   ├── Camera.jsx          # Webcam component
│   │   └── Loading.jsx         # Loading spinner
│   │
│   ├── services/
│   │   └── api.js              # Axios API calls
│   │
│   ├── context/
│   │   └── AuthContext.jsx     # Authentication state
│   │
│   ├── utils/
│   │   └── helpers.js          # Helper functions
│   │
│   ├── App.jsx                 # Main app with routing
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
│
├── package.json
├── tailwind.config.js
└── vite.config.js
```

## 🔑 Pages & Routes

### Public Routes
- `/login` - Login page
- `/register` - Registration page

### Protected Routes
- `/dashboard` - User dashboard
- `/attendance` - Mark attendance
- `/register-face` - Face registration

### Admin Routes
- `/admin` - Admin dashboard (admin only)

## 📸 Camera Features

### Face Registration
- Capture 5-10 photos dari berbagai sudut
- Live camera preview
- Photo preview sebelum upload
- Retake option
- Progress indicator

### Attendance
- Single photo capture
- Real-time verification
- Confidence score display
- Auto attendance recording

## 🔐 Authentication

- JWT-based authentication
- Access token (1 hour)
- Refresh token (7 days)
- Auto token refresh
- Protected routes
- Role-based access (student, teacher, admin)

## 🎯 API Integration

Backend API: `http://localhost:5000/api`

### Endpoints Used
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - Logout
- `POST /auth/refresh` - Refresh token
- `GET /user/profile` - Get profile
- `POST /face/register` - Register face (multi-photo)
- `POST /face/verify` - Verify face
- `GET /face/status` - Face registration status
- `GET /attendance/history` - Attendance history
- `GET /attendance/stats` - Statistics
- `GET /attendance/all` - All attendance (admin)
- `GET /face/stats` - Face stats (admin)

## 🎨 UI Components

### Buttons
```jsx
<button className="btn btn-primary">Primary Button</button>
<button className="btn btn-secondary">Secondary Button</button>
<button className="btn btn-outline">Outline Button</button>
<button className="btn btn-danger">Danger Button</button>
```

### Inputs
```jsx
<input className="input" placeholder="Enter text" />
```

### Cards
```jsx
<div className="card">
  <h2>Card Title</h2>
  <p>Card content</p>
</div>
```

### Badges
```jsx
<span className="badge badge-success">Success</span>
<span className="badge badge-error">Error</span>
<span className="badge badge-warning">Warning</span>
```

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints:
  - `sm`: 640px
  - `md`: 768px
  - `lg`: 1024px
  - `xl`: 1280px

## 🔧 Development

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Lint Code

```bash
npm run lint
```

## 🌐 Environment Variables

Tidak ada environment variables yang diperlukan. API base URL sudah dikonfigurasi di `vite.config.js` dengan proxy.

Jika ingin mengubah backend URL, edit `src/services/api.js`:

```javascript
const api = axios.create({
  baseURL: 'http://your-backend-url/api',
});
```

## 📝 Usage Flow

### 1. Register & Login
1. Buka `/register`
2. Isi form registrasi
3. Otomatis redirect ke `/register-face`

### 2. Face Registration
1. Klik "Start Camera"
2. Capture 5-10 foto dari berbagai sudut
3. Review photos
4. Submit untuk registrasi

### 3. Mark Attendance
1. Buka `/attendance`
2. Klik "Capture Photo"
3. Ambil foto wajah
4. Sistem akan verify dan record attendance

### 4. View Dashboard
1. Lihat statistics
2. Check face registration status
3. View recent attendance history

## 🎯 Best Practices

### Camera Usage
- Pastikan pencahayaan yang baik
- Wajah harus jelas terlihat
- Hanya 1 wajah dalam frame
- Tidak menggunakan kacamata hitam atau masker

### Face Registration
- Capture minimal 5 foto
- Gunakan berbagai sudut (frontal, slight left, slight right)
- Berbagai ekspresi (normal, senyum)
- Konsisten dengan kondisi pencahayaan

## 🐛 Troubleshooting

### Camera Not Working
- Allow camera permission di browser
- Check browser compatibility
- Pastikan tidak ada aplikasi lain yang menggunakan camera

### API Connection Error
- Pastikan backend running di http://localhost:5000
- Check CORS configuration di backend
- Verify network connection

### Token Expired
- Token akan auto-refresh
- Jika gagal, akan auto-redirect ke login

## 🚀 Deployment

### Vercel/Netlify
1. Build project: `npm run build`
2. Deploy folder `dist/`
3. Configure environment variables jika perlu

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 📄 License

This project is for educational purposes.

---

**Happy Coding! 🚀**
