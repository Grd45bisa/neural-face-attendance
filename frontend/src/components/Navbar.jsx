import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Home, Camera, LayoutDashboard, Users } from 'lucide-react';

const Navbar = () => {
    const { user, logout, isAdmin } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const isActive = (path) => {
        return location.pathname === path;
    };

    if (!user) return null;

    return (
        <nav className="bg-white border-b border-border sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    {/* Logo & Navigation */}
                    <div className="flex items-center space-x-8">
                        <Link to="/dashboard" className="flex items-center space-x-2">
                            <Camera className="w-6 h-6 text-primary" />
                            <span className="font-bold text-xl text-text">Face Attendance</span>
                        </Link>

                        <div className="hidden md:flex space-x-4">
                            <Link
                                to="/dashboard"
                                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${isActive('/dashboard')
                                        ? 'bg-primary text-white'
                                        : 'text-text hover:bg-gray-100'
                                    }`}
                            >
                                <Home className="w-4 h-4" />
                                <span>Dashboard</span>
                            </Link>

                            <Link
                                to="/attendance"
                                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${isActive('/attendance')
                                        ? 'bg-primary text-white'
                                        : 'text-text hover:bg-gray-100'
                                    }`}
                            >
                                <Camera className="w-4 h-4" />
                                <span>Attendance</span>
                            </Link>

                            {isAdmin && (
                                <Link
                                    to="/admin"
                                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${isActive('/admin')
                                            ? 'bg-primary text-white'
                                            : 'text-text hover:bg-gray-100'
                                        }`}
                                >
                                    <Users className="w-4 h-4" />
                                    <span>Admin</span>
                                </Link>
                            )}
                        </div>
                    </div>

                    {/* User Menu */}
                    <div className="flex items-center space-x-4">
                        <div className="hidden md:flex items-center space-x-3">
                            <User className="w-5 h-5 text-text" />
                            <div className="text-sm">
                                <p className="font-medium text-text">{user.name}</p>
                                <p className="text-gray-500 text-xs">{user.role}</p>
                            </div>
                        </div>

                        <button
                            onClick={handleLogout}
                            className="flex items-center space-x-2 px-4 py-2 text-error hover:bg-red-50 rounded-lg transition-colors"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="hidden md:inline">Logout</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Navigation */}
            <div className="md:hidden border-t border-border">
                <div className="flex justify-around py-2">
                    <Link
                        to="/dashboard"
                        className={`flex flex-col items-center px-3 py-2 ${isActive('/dashboard') ? 'text-primary' : 'text-gray-500'
                            }`}
                    >
                        <Home className="w-5 h-5" />
                        <span className="text-xs mt-1">Dashboard</span>
                    </Link>

                    <Link
                        to="/attendance"
                        className={`flex flex-col items-center px-3 py-2 ${isActive('/attendance') ? 'text-primary' : 'text-gray-500'
                            }`}
                    >
                        <Camera className="w-5 h-5" />
                        <span className="text-xs mt-1">Attendance</span>
                    </Link>

                    {isAdmin && (
                        <Link
                            to="/admin"
                            className={`flex flex-col items-center px-3 py-2 ${isActive('/admin') ? 'text-primary' : 'text-gray-500'
                                }`}
                        >
                            <Users className="w-5 h-5" />
                            <span className="text-xs mt-1">Admin</span>
                        </Link>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
