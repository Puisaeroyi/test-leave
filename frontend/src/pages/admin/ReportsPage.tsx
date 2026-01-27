import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { hrApi } from '../../api/users';

interface DepartmentReport {
  department: string;
  total_users: number;
  total_allocated: number;
  total_used: number;
  total_remaining: number;
}

export default function ReportsPage() {
  const [selectedYear] = useState(new Date().getFullYear().toString());

  const { data: users } = useQuery({
    queryKey: ['hr-users'],
    queryFn: () => hrApi.getUsers(),
  });

  const { data: departments } = useQuery({
    queryKey: ['hr-departments'],
    queryFn: () => hrApi.getDepartments(),
  });

  // Generate department reports (using 0 for balance fields since they're not on User type)
  const departmentReports: DepartmentReport[] = departments?.map((dept) => {
    const deptUsers = users?.filter((u) => u.department === dept.id) || [];
    return {
      department: dept.name,
      total_users: deptUsers.length,
      total_allocated: 0,  // Would need balance API to populate
      total_used: 0,       // Would need balance API to populate
      total_remaining: 0,  // Would need balance API to populate
    };
  }) || [];

  const exportToCSV = () => {
    const headers = ['Department', 'Total Users', 'Allocated Hours', 'Used Hours', 'Remaining Hours'];
    const rows = departmentReports.map((r) => [
      r.department,
      r.total_users,
      r.total_allocated,
      r.total_used,
      r.total_remaining,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leave-report-${selectedYear}.csv`;
    a.click();
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Reports</h1>

      <div className="flex justify-between items-center mb-6">
        <select
          className="border rounded px-3 py-2"
          value={selectedYear}
          disabled
        >
          <option value="2026">2026</option>
          <option value="2025">2025</option>
          <option value="2024">2024</option>
        </select>

        <button
          onClick={exportToCSV}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Export CSV
        </button>
      </div>

      {/* Department Report */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Leave Balance by Department</h2>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Department
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Total Users
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Allocated Hours
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Used Hours
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Remaining Hours
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Usage %
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {departmentReports.map((report) => (
              <tr key={report.department}>
                <td className="px-6 py-4 whitespace-nowrap font-medium">
                  {report.department}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">{report.total_users}</td>
                <td className="px-6 py-4 whitespace-nowrap">{report.total_allocated}</td>
                <td className="px-6 py-4 whitespace-nowrap">{report.total_used}</td>
                <td className="px-6 py-4 whitespace-nowrap">{report.total_remaining}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {report.total_allocated > 0
                    ? ((report.total_used / report.total_allocated) * 100).toFixed(1)
                    : 0}
                  %
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Users</h3>
          <p className="text-3xl font-bold mt-2">{users?.length || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Departments</h3>
          <p className="text-3xl font-bold mt-2">{departments?.length || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Active Users</h3>
          <p className="text-3xl font-bold mt-2">
            {users?.filter((u) => u.status === 'ACTIVE').length || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Year</h3>
          <p className="text-3xl font-bold mt-2">{selectedYear}</p>
        </div>
      </div>
    </div>
  );
}
