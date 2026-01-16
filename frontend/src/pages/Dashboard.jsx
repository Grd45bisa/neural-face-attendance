import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { User, Camera, Calendar, Clock, CheckCircle2 } from 'lucide-react';
import { faceAPI, attendanceAPI } from '../services/api';
import { formatDate, formatTime, getStatusBadgeClass } from '../utils/helpers';
import toast from 'react-hot-toast';

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [faceStatus, setFaceStatus] = useState(null);
    const [attendanceHistory, setAttendanceHistory] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [faceRes, historyRes, statsRes] = await Promise.all([
                faceAPI.getFaceStatus(),
                attendanceAPI.getHistory({ page: 1, per_page: 5 }),
                attendanceAPI.getStats(),
            ]);

            setFaceStatus(faceRes.data.data);
            setAttendanceHistory(historyRes.data.data);
            setStats(statsRes.data.data);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <div className="flex items-center justify-center h-96">
                    <div className="text-center">
                        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                        <p className="text-gray-600">Loading...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-text">Dashboard</h1>
                    <p className="mt-2 text-gray-600">Welcome back, {user.name}!</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Total Attendance</p>
                                <p className="text-3xl font-bold text-text mt-1">
                                    {stats?.total || 0}
                                </p>
                            </div>
                            <div className="bg-primary bg-opacity-10 p-3 rounded-lg">
                                <Calendar className="w-8 h-8 text-primary" />
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Check-ins</p>
                                <p className="text-3xl font-bold text-text mt-1">
                                    {stats?.check_ins || 0}
                                </p>
                            </div>
                            <div className="bg-success bg-opacity-10 p-3 rounded-lg">
                                <CheckCircle2 className="w-8 h-8 text-success" />
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Face Method</p>
                                <p className="text-3xl font-bold text-text mt-1">
                                    {stats?.face_method || 0}
                                </p>
                            </div>
                            <div className="bg-secondary bg-opacity-10 p-3 rounded-lg">
                                <Camera className="w-8 h-8 text-secondary" />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Profile Card */}
                    <div className="lg:col-span-1">
                        <div className="card">
                            <h2 className="text-xl font-semibold text-text mb-4">Profile</h2>

                            <div className="space-y-4">
                                <div className="flex items-center space-x-3">
                                    <div className="bg-primary bg-opacity-10 p-3 rounded-lg">
                                        <User className="w-6 h-6 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Name</p>
                                        <p className="font-medium text-text">{user.name}</p>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-3">
                                    <div className="bg-primary bg-opacity-10 p-3 rounded-lg">
                                        <User className="w-6 h-6 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Email</p>
                                        <p className="font-medium text-text">{user.email}</p>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-3">
                                    <div className="bg-primary bg-opacity-10 p-3 rounded-lg">
                                        <Camera className="w-6 h-6 text-primary" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm text-gray-600">Face Registration</p>
                                        <div className="flex items-center justify-between mt-1">
                                            <span className={`badge ${faceStatus?.face_registered ? 'badge-success' : 'badge-warning'}`}>
                                                {faceStatus?.face_registered ? 'Registered' : 'Not Registered'}
                                            </span>
                                            {!faceStatus?.face_registered && (
                                                <button
                                                    onClick={() => navigate('/register-face')}
                                                    className="text-primary text-sm hover:underline"
                                                >
                                                    Register Now
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Attendance History */}
                    <div className="lg:col-span-2">
                        <div className="card">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-semibold text-text">Recent Attendance</h2>
                                <button
                                    onClick={() => navigate('/attendance')}
                                    className="text-primary hover:underline text-sm"
                                >
                                    Mark Attendance
                                </button>
                            </div>

                            {attendanceHistory.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                    <p>No attendance records yet</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {attendanceHistory.map((record) => (
                                        <div
                                            key={record._id}
                                            className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                                        >
                                            <div className="flex items-center space-x-3">
                                                <div className={`p-2 rounded-lg ${record.type === 'check-in' ? 'bg-success bg-opacity-10' : 'bg-blue-100'
                                                    }`}>
                                                    <Clock className={`w-5 h-5 ${record.type === 'check-in' ? 'text-success' : 'text-blue-600'
                                                        }`} />
                                                </div>
                                                <div>
                                                    <p className="font-medium text-text capitalize">{record.type}</p>
                                                    <p className="text-sm text-gray-600">
                                                        {formatDate(record.timestamp)} at {formatTime(record.timestamp)}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="text-right">
                                                <span className={`badge ${getStatusBadgeClass(record.status)}`}>
                                                    {record.status}
                                                </span>
                                                <p className="text-xs text-gray-500 mt-1 capitalize">{record.method}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
