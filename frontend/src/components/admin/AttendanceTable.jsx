import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AttendanceTable = ({ onUpdate }) => {
    const [attendance, setAttendance] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [classFilter, setClassFilter] = useState('');

    useEffect(() => {
        loadAttendance();
    }, [selectedDate, classFilter]);

    const loadAttendance = async () => {
        try {
            setLoading(true);
            const params = { date: selectedDate };
            if (classFilter) params.class = classFilter;

            const response = await axios.get('/api/admin/attendance/daily', { params });
            setAttendance(response.data.data.records);

            if (onUpdate) onUpdate();
        } catch (error) {
            toast.error('Failed to load attendance');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'present': return 'badge-success';
            case 'late': return 'badge-warning';
            case 'absent': return 'badge-error';
            default: return 'badge-warning';
        }
    };

    return (
        <div className="card">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 space-y-4 md:space-y-0">
                <h3 className="text-xl font-semibold text-text">Daily Attendance</h3>

                <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-3">
                    {/* Date Picker */}
                    <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="input pl-10"
                        />
                    </div>

                    {/* Class Filter */}
                    <input
                        type="text"
                        placeholder="Filter by class..."
                        value={classFilter}
                        onChange={(e) => setClassFilter(e.target.value)}
                        className="input"
                    />
                </div>
            </div>

            {/* Table */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
            ) : attendance.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No attendance records for this date</p>
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-border">
                            <tr>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-text">Name</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-text">NIS</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-text">Class</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-text">Check-in Time</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-text">Status</th>
                                <th className="px-4 py-3 text-left text-sm font-semibold text-text">Confidence</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {attendance.map((record, index) => (
                                <tr key={index} className="hover:bg-gray-50">
                                    <td className="px-4 py-3 text-sm text-text">{record.name}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600">{record.nis || '-'}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600">{record.class || '-'}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {record.check_in_time ? new Date(record.check_in_time).toLocaleTimeString() : '-'}
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                        <span className={`badge ${getStatusColor(record.status)}`}>
                                            {record.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">
                                        {record.confidence ? `${(record.confidence * 100).toFixed(1)}%` : '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default AttendanceTable;
