import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Users, Calendar, FileText, Settings, Menu, X } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

// Components
import UserTable from '../components/admin/UserTable';
import AttendanceTable from '../components/admin/AttendanceTable';
import StatisticsCard from '../components/admin/StatisticsCard';
import AttendanceReport from '../components/admin/AttendanceReport';

const AdminDashboard = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('users');
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [stats, setStats] = useState({
        totalStudents: 0,
        presentToday: 0,
        lateToday: 0,
        absentToday: 0
    });

    useEffect(() => {
        loadDailyStats();
    }, []);

    const loadDailyStats = async () => {
        try {
            const response = await axios.get('/api/admin/attendance/daily');
            const data = response.data.data;

            setStats({
                totalStudents: data.statistics.total,
                presentToday: data.statistics.present,
                lateToday: data.statistics.late,
                absentToday: data.statistics.absent
            });
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    };

    const menuItems = [
        { id: 'users', label: 'User Management', icon: Users },
        { id: 'attendance', label: 'Daily Attendance', icon: Calendar },
        { id: 'reports', label: 'Reports', icon: FileText },
        { id: 'settings', label: 'Settings', icon: Settings }
    ];

    return (
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar */}
            <aside className={`bg-white border-r border-border transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-0 md:w-20'
                }`}>
                <div className="h-full flex flex-col">
                    {/* Logo */}
                    <div className="p-4 border-b border-border flex items-center justify-between">
                        {sidebarOpen && (
                            <h1 className="text-xl font-bold text-text">Admin Panel</h1>
                        )}
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="p-2 hover:bg-gray-100 rounded-lg md:hidden"
                        >
                            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 p-4">
                        <ul className="space-y-2">
                            {menuItems.map((item) => {
                                const Icon = item.icon;
                                return (
                                    <li key={item.id}>
                                        <button
                                            onClick={() => setActiveTab(item.id)}
                                            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${activeTab === item.id
                                                    ? 'bg-primary text-white'
                                                    : 'text-text hover:bg-gray-100'
                                                }`}
                                        >
                                            <Icon className="w-5 h-5" />
                                            {sidebarOpen && <span>{item.label}</span>}
                                        </button>
                                    </li>
                                );
                            })}
                        </ul>
                    </nav>

                    {/* User Info */}
                    {sidebarOpen && (
                        <div className="p-4 border-t border-border">
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-semibold">
                                    {user?.name?.charAt(0).toUpperCase()}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-text truncate">{user?.name}</p>
                                    <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                {/* Top Bar */}
                <div className="bg-white border-b border-border p-4 sticky top-0 z-10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => setSidebarOpen(!sidebarOpen)}
                                className="p-2 hover:bg-gray-100 rounded-lg hidden md:block"
                            >
                                <Menu className="w-5 h-5" />
                            </button>
                            <h2 className="text-2xl font-bold text-text">
                                {menuItems.find(item => item.id === activeTab)?.label}
                            </h2>
                        </div>
                        <div className="text-sm text-gray-600">
                            {new Date().toLocaleDateString('id-ID', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
                        </div>
                    </div>
                </div>

                {/* Content Area */}
                <div className="p-6">
                    {/* Statistics Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                        <StatisticsCard
                            title="Total Students"
                            value={stats.totalStudents}
                            icon={Users}
                            color="blue"
                        />
                        <StatisticsCard
                            title="Present Today"
                            value={stats.presentToday}
                            icon={Calendar}
                            color="green"
                        />
                        <StatisticsCard
                            title="Late Today"
                            value={stats.lateToday}
                            icon={Calendar}
                            color="yellow"
                        />
                        <StatisticsCard
                            title="Absent Today"
                            value={stats.absentToday}
                            icon={Calendar}
                            color="red"
                        />
                    </div>

                    {/* Tab Content */}
                    {activeTab === 'users' && <UserTable />}
                    {activeTab === 'attendance' && <AttendanceTable onUpdate={loadDailyStats} />}
                    {activeTab === 'reports' && <AttendanceReport />}
                    {activeTab === 'settings' && (
                        <div className="card text-center py-12">
                            <Settings className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                            <h3 className="text-lg font-semibold text-text mb-2">Settings</h3>
                            <p className="text-gray-600">Settings page coming soon...</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default AdminDashboard;
