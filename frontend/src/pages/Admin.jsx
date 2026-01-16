import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { Users, Calendar, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { attendanceAPI, faceAPI } from '../services/api';
import { formatDate, formatTime, getStatusBadgeClass } from '../utils/helpers';

const Admin = () => {
    const [attendanceList, setAttendanceList] = useState([]);
    const [stats, setStats] = useState(null);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, [selectedDate]);

    const loadData = async () => {
        try {
            const [attendanceRes, statsRes] = await Promise.all([
                attendanceAPI.getAllAttendance({ date: selectedDate }),
                faceAPI.getStats(),
            ]);

            setAttendanceList(attendanceRes.data.data.records);
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
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-bold text-text mb-8">Admin Dashboard</h1>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Registered Faces</p>
                                <p className="text-3xl font-bold text-text mt-1">
                                    {stats?.total_registered || 0}
                                </p>
                            </div>
                            <Users className="w-8 h-8 text-primary" />
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Total Verifications</p>
                                <p className="text-3xl font-bold text-text mt-1">
                                    {stats?.total_verifications || 0}
                                </p>
                            </div>
                            <CheckCircle2 className="w-8 h-8 text-success" />
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600">Avg Photos/User</p>
                                <p className="text-3xl font-bold text-text mt-1">
                                    {stats?.avg_photos_per_user || 0}
                                </p>
                            </div>
                            <Calendar className="w-8 h-8 text-secondary" />
                        </div>
                    </div>
                </div>

                {/* Attendance List */}
                <div className="card">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold text-text">Daily Attendance</h2>
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="input w-auto"
                        />
                    </div>

                    {attendanceList.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No attendance records for this date</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-border">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Student</th>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Email</th>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Time</th>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Type</th>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Method</th>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Confidence</th>
                                        <th className="px-4 py-3 text-left text-sm font-semibold text-text">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {attendanceList.map((record) => (
                                        <tr key={record._id} className="hover:bg-gray-50">
                                            <td className="px-4 py-3 text-sm text-text">{record.user_name || 'N/A'}</td>
                                            <td className="px-4 py-3 text-sm text-gray-600">{record.user_email || 'N/A'}</td>
                                            <td className="px-4 py-3 text-sm text-text">{formatTime(record.timestamp)}</td>
                                            <td className="px-4 py-3 text-sm">
                                                <span className="capitalize">{record.type}</span>
                                            </td>
                                            <td className="px-4 py-3 text-sm">
                                                <span className="capitalize">{record.method}</span>
                                            </td>
                                            <td className="px-4 py-3 text-sm">
                                                {record.confidence ? `${(record.confidence * 100).toFixed(1)}%` : '-'}
                                            </td>
                                            <td className="px-4 py-3 text-sm">
                                                <span className={`badge ${getStatusBadgeClass(record.status)}`}>
                                                    {record.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Admin;
