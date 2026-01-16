/**
 * API Service Layer
 * Handles all HTTP requests to the backend
 */

import axios from 'axios';
import toast from 'react-hot-toast';

// Create axios instance
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - handle errors and token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken) {
                    const response = await axios.post(`${import.meta.env.VITE_API_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token } = response.data.data;
                    localStorage.setItem('access_token', access_token);

                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return api(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed, logout user
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        // Show error toast
        const message = error.response?.data?.message || 'An error occurred';
        toast.error(message);

        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    logout: (refreshToken) => api.post('/auth/logout', { refresh_token: refreshToken }),
    refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
};

// User API
export const userAPI = {
    getProfile: () => api.get('/user/profile'),
    updateProfile: (data) => api.put('/user/profile', data),
    changePassword: (data) => api.put('/user/password', data),
};

// Face API
export const faceAPI = {
    registerFace: (photos) => {
        const formData = new FormData();
        photos.forEach((photo) => {
            formData.append('photos', photo);
        });
        return api.post('/face/register', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    verifyFace: (photo) => {
        const formData = new FormData();
        formData.append('photo', photo);
        return api.post('/face/verify', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    recognizeFace: (photo) => {
        const formData = new FormData();
        formData.append('photo', photo);
        return api.post('/face/recognize', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    getFaceStatus: () => api.get('/face/status'),
    deleteFace: () => api.delete('/face/delete'),
    getStats: () => api.get('/face/stats'),
};

// Attendance API
export const attendanceAPI = {
    checkIn: (data) => api.post('/attendance/check-in', data),
    checkOut: (data) => api.post('/attendance/check-out', data),
    getHistory: (params) => api.get('/attendance/history', { params }),
    getToday: () => api.get('/attendance/today'),
    getStats: (params) => api.get('/attendance/stats', { params }),
    getLatest: () => api.get('/attendance/latest'),

    // Admin
    getAllAttendance: (params) => api.get('/attendance/all', { params }),
    verifyAttendance: (id, status) => api.put(`/attendance/${id}/verify`, { status }),
    deleteAttendance: (id) => api.delete(`/attendance/${id}`),
    getReport: (params) => api.get('/attendance/report', { params }),
};

export default api;
