import { useState } from 'react';
import { Download, FileText } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AttendanceReport = () => {
    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [year, setYear] = useState(new Date().getFullYear());
    const [classFilter, setClassFilter] = useState('');
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [exporting, setExporting] = useState(false);

    const loadReport = async () => {
        try {
            setLoading(true);
            const params = { month, year };
            if (classFilter) params.class = classFilter;

            const response = await axios.get('/api/admin/attendance/report', { params });
            setReport(response.data.data);
        } catch (error) {
            toast.error('Failed to load report');
        } finally {
            setLoading(false);
        }
    };

    const exportToExcel = async () => {
        try {
            setExporting(true);

            // Calculate date range for the month
            const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
            const lastDay = new Date(year, month, 0).getDate();
            const endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;

            const response = await axios.post('/api/admin/export/excel', {
                start_date: startDate,
                end_date: endDate,
                class: classFilter || undefined
            }, {
                responseType: 'blob'
            });

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `attendance_report_${year}_${month}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();

            toast.success('Report exported successfully');
        } catch (error) {
            toast.error('Failed to export report');
        } finally {
            setExporting(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="card">
                <h3 className="text-xl font-semibold text-text mb-4">Generate Report</h3>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-text mb-2">Month</label>
                        <select
                            value={month}
                            onChange={(e) => setMonth(parseInt(e.target.value))}
                            className="input"
                        >
                            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                                <option key={m} value={m}>
                                    {new Date(2024, m - 1).toLocaleString('default', { month: 'long' })}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text mb-2">Year</label>
                        <select
                            value={year}
                            onChange={(e) => setYear(parseInt(e.target.value))}
                            className="input"
                        >
                            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map((y) => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text mb-2">Class (Optional)</label>
                        <input
                            type="text"
                            placeholder="e.g., XII-IPA-1"
                            value={classFilter}
                            onChange={(e) => setClassFilter(e.target.value)}
                            className="input"
                        />
                    </div>

                    <div className="flex items-end space-x-2">
                        <button
                            onClick={loadReport}
                            className="btn btn-primary flex-1"
                            disabled={loading}
                        >
                            {loading ? 'Loading...' : 'Generate'}
                        </button>
                        <button
                            onClick={exportToExcel}
                            className="btn btn-secondary"
                            disabled={exporting}
                            title="Export to Excel"
                        >
                            <Download className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Report Table */}
            {report && (
                <div className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xl font-semibold text-text">
                            Report for {new Date(year, month - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}
                        </h3>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-border">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Name</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">NIS</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold text-text">Class</th>
                                    <th className="px-4 py-3 text-center text-sm font-semibold text-text">Present</th>
                                    <th className="px-4 py-3 text-center text-sm font-semibold text-text">Late</th>
                                    <th className="px-4 py-3 text-center text-sm font-semibold text-text">Absent</th>
                                    <th className="px-4 py-3 text-center text-sm font-semibold text-text">Percentage</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {report.report.map((record, index) => (
                                    <tr key={index} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 text-sm text-text">{record.name}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{record.nis || '-'}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{record.class || '-'}</td>
                                        <td className="px-4 py-3 text-sm text-center text-success font-semibold">
                                            {record.present}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-center text-warning font-semibold">
                                            {record.late}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-center text-error font-semibold">
                                            {record.absent}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-center">
                                            <span className={`badge ${record.percentage >= 80 ? 'badge-success' :
                                                    record.percentage >= 60 ? 'badge-warning' :
                                                        'badge-error'
                                                }`}>
                                                {record.percentage}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AttendanceReport;
