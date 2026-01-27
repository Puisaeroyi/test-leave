import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { leavesApi } from '../../api/leaves';
import LeaveBalanceCard from '../../components/leaves/LeaveBalanceCard';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';

const statusColors: Record<string, 'approved' | 'pending' | 'rejected' | 'cancelled' | 'info'> = {
  APPROVED: 'approved',
  PENDING: 'pending',
  REJECTED: 'rejected',
  CANCELLED: 'cancelled',
};

export default function DashboardPage() {
  const currentYear = new Date().getFullYear();

  // Fetch leave balance
  const { data: balance } = useQuery({
    queryKey: ['leaveBalance', currentYear],
    queryFn: () => leavesApi.getMyLeaveBalance(currentYear),
  });

  // Fetch recent requests
  const { data: requests, isLoading: requestsLoading } = useQuery({
    queryKey: ['leaveRequests', 'recent'],
    queryFn: () => leavesApi.getLeaveRequests({}),
  });

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const recentRequests = requests?.slice(0, 5) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Welcome back! Here's your leave overview.</p>
      </div>

      {/* Balance and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leave Balance Card */}
        <div className="lg:col-span-2">
          <LeaveBalanceCard year={currentYear} />
        </div>

        {/* Quick Actions */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Button variant="primary" className="w-full" asChild>
              <Link to="/leaves/new">+ New Leave Request</Link>
            </Button>
            <Button variant="secondary" className="w-full" asChild>
              <Link to="/leaves">View All Requests</Link>
            </Button>
            <Button variant="ghost" className="w-full" asChild>
              <Link to="/calendar">Team Calendar</Link>
            </Button>
          </div>
        </Card>
      </div>

      {/* Recent Requests */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Requests</h2>
          <Link
            to="/leaves"
            className="text-sm text-red-600 hover:text-red-700 font-medium"
          >
            View all →
          </Link>
        </div>

        {requestsLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-gray-200 rounded-lg"></div>
              </div>
            ))}
          </div>
        ) : recentRequests.length === 0 ? (
          <div className="text-center py-8">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No requests yet</h3>
            <p className="mt-2 text-gray-500">Create your first leave request to get started.</p>
            <div className="mt-6">
              <Button variant="primary" asChild>
                <Link to="/leaves/new">+ New Request</Link>
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {recentRequests.map((request: any) => (
              <div
                key={request.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    {request.category && (
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: request.category.color }}
                      />
                    )}
                    <p className="text-sm font-medium text-gray-900">
                      {request.start_date === request.end_date
                        ? formatDate(request.start_date)
                        : `${formatDate(request.start_date)} - ${formatDate(request.end_date)}`}
                    </p>
                    <Badge variant={statusColors[request.status] || 'info'}>
                      {request.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {request.total_hours}h
                    {request.reason && ` • ${request.reason}`}
                  </p>
                </div>
                <Link
                  to={`/leaves/${request.id}`}
                  className="text-sm text-red-600 hover:text-red-700 font-medium"
                >
                  View
                </Link>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Balance Summary */}
      {balance && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-4">
            <div className="text-sm text-gray-600 mb-1">Allocated</div>
            <div className="text-2xl font-bold text-gray-900">
              {balance.allocated_hours}h
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-600 mb-1">Used</div>
            <div className="text-2xl font-bold text-red-600">
              {balance.used_hours}h
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-600 mb-1">Remaining</div>
            <div className="text-2xl font-bold text-green-600">
              {balance.remaining_hours}h
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
