import { useState, useEffect } from 'react';
import { Search, Edit2, Trash2, UserPlus } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const UserTable = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        loadUsers();
    }, [page, search, roleFilter]);

    const loadUsers = async () => {
        try {
            setLoading(true);
            const params = { page, per_page: 10 };
            if (search) params.search = search;
            if (roleFilter) params.role = roleFilter;

            const response = await axios.get('/api/admin/users', { params });
            setUsers(response.data.data);
            setTotalPages(response.data.pagination.total_pages);
        } catch (error) {
            toast.error('Failed to load users');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (userId) => {
        if (!confirm('Are you sure you want to delete this user?')) return;

        try {
            await axios.delete(`/api/admin/users/${userId}`);
            toast.success('User deleted successfully');
            loadUsers();
        } catch (error) {
            toast.error('Failed to delete user');
        }
    };

    return (
        <div className="card">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 space-y-4 md:space-y-0">
                <h3 className="text-xl font-semibold text-text">User Management</h3>

                <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-3">
                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search by name or NIS..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="input pl-10 w-full md:w-64"
                        />
                    </div>

                    {/* Role Filter */}
                    <select
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                        className="input w-full md:w-auto"
                    >
                        <option value="">All Roles</option>
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
            </div>

            {/* Table */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
            ) : users.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    <p>No users found</p>
                </div>
            ) : (
                <>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-border">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Name</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">NIS</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Email</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Class</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Role</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Face</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {users.map((user) => (
                                    <tr key={user.user_id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 text-sm text-text">{user.full_name || user.name}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{user.nis || '-'}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{user.class_name || '-'}</td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className="badge badge-success capitalize">{user.role}</span>
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className={`badge ${user.is_face_registered || user.face_registered ? 'badge-success' : 'badge-warning'}`}>
                                                {user.is_face_registered || user.face_registered ? 'Registered' : 'Not Registered'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            <div className="flex items-center space-x-2">
                                                <button
                                                    onClick={() => toast.info('Edit feature coming soon')}
                                                    className="p-2 text-primary hover:bg-blue-50 rounded-lg"
                                                >
                                                    <Edit2 className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(user.user_id)}
                                                    className="p-2 text-error hover:bg-red-50 rounded-lg"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between mt-6">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="btn btn-outline"
                            >
                                Previous
                            </button>
                            <span className="text-sm text-gray-600">
                                Page {page} of {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="btn btn-outline"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default UserTable;
