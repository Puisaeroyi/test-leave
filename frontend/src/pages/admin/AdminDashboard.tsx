import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { hrApi } from '../../api/users';

export default function AdminDashboard() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({ role: '', department: '', status: '' });

  const { data: users, isLoading } = useQuery({
    queryKey: ['hr-users', filters],
    queryFn: () => hrApi.getUsers(filters),
  });

  // const { data: departments } = useQuery({
  //   queryKey: ['hr-departments'],
  //   queryFn: () => hrApi.getDepartments(),
  // });

  const setupMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) =>
      hrApi.setupUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-users'] });
      alert('User setup completed!');
    },
  });

  const adjustBalanceMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) =>
      hrApi.adjustBalance(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-users'] });
      alert('Balance adjusted!');
    },
  });

  const handleSetupUser = (userId: string) => {
    const department = prompt('Enter department ID:');
    const role = prompt('Enter role (EMPLOYEE/MANAGER/HR/ADMIN):', 'EMPLOYEE');
    const allocated = prompt('Enter allocated hours:', '96');

    if (department && role && allocated) {
      setupMutation.mutate({
        userId,
        data: {
          department_id: department,
          role,
          allocated_hours: parseFloat(allocated),
        },
      });
    }
  };

  const handleAdjustBalance = (userId: string) => {
    const allocated = prompt('Enter new allocated hours:');
    const reason = prompt('Enter reason:');

    if (allocated && reason) {
      adjustBalanceMutation.mutate({
        userId,
        data: {
          allocated_hours: parseFloat(allocated),
          reason,
        },
      });
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">HR Admin Dashboard</h1>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6 flex gap-4">
        <select
          className="border rounded px-3 py-2"
          value={filters.role}
          onChange={(e) => setFilters({ ...filters, role: e.target.value })}
        >
          <option value="">All Roles</option>
          <option value="EMPLOYEE">Employee</option>
          <option value="MANAGER">Manager</option>
          <option value="HR">HR</option>
          <option value="ADMIN">Admin</option>
        </select>

        <select
          className="border rounded px-3 py-2"
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </div>

      {/* Users Table */}
      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Onboarded
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users?.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.first_name} {user.last_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        user.status === 'ACTIVE'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.department_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.has_completed_onboarding ? 'Yes' : 'No'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleSetupUser(user.id)}
                      className="text-blue-600 hover:underline mr-2"
                    >
                      Setup
                    </button>
                    <button
                      onClick={() => handleAdjustBalance(user.id)}
                      className="text-green-600 hover:underline"
                    >
                      Adjust Balance
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
