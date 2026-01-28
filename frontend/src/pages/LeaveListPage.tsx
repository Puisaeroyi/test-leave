import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { leavesApi } from '../api/leaves';
import type { LeaveRequest } from '../types';

export default function LeaveListPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeNav, setActiveNav] = useState('leaves');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<LeaveRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED'>('ALL');

  useEffect(() => {
    fetchLeaveRequests();
  }, []);

  useEffect(() => {
    if (statusFilter === 'ALL') {
      setFilteredRequests(leaveRequests);
    } else {
      setFilteredRequests(leaveRequests.filter(req => req.status === statusFilter));
    }
  }, [statusFilter, leaveRequests]);

  const fetchLeaveRequests = async () => {
    try {
      setIsLoading(true);
      const requests = await leavesApi.getLeaveRequests();
      setLeaveRequests(requests);
    } catch (error) {
      console.error('Failed to fetch leave requests:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Parse date string as local date to avoid timezone shift
  const parseLocalDate = (dateStr: string): Date => {
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(year, month - 1, day);
  };

  const formatDate = (dateStr: string) => {
    const date = parseLocalDate(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hour12 = hours % 12 || 12;
    return `${hour12}:${minutes.toString().padStart(2, '0')} ${ampm}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'text-green-600 bg-green-50';
      case 'PENDING': return 'text-yellow-600 bg-yellow-50';
      case 'REJECTED': return 'text-red-600 bg-red-50';
      case 'CANCELLED': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const handleCancel = async (requestId: string) => {
    if (!confirm('Are you sure you want to cancel this leave request?')) return;

    try {
      await leavesApi.cancelLeaveRequest(requestId);
      setLeaveRequests(prev => prev.map(r =>
        r.id === requestId ? { ...r, status: 'CANCELLED' as const } : r
      ));
    } catch (error) {
      console.error('Failed to cancel request:', error);
      alert('Failed to cancel request. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-200 border-t-red-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading leave requests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex">
      {/* Left Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white shadow-md z-10 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <img src="/teampl.ico" alt="TeamPL" className="w-48 h-auto" />
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <button
            onClick={() => { setActiveNav('new-leave'); navigate('/leaves/new'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'new-leave' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Request
          </button>

          <button
            onClick={() => { setActiveNav('dashboard'); navigate('/'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'dashboard' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            Dashboard
          </button>

          <button
            onClick={() => { setActiveNav('leaves'); navigate('/leaves'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'leaves' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            My Requests
          </button>

          <button
            onClick={() => { setActiveNav('calendar'); navigate('/calendar'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'calendar' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Team Calendar
          </button>

          {(user?.role === 'MANAGER' || user?.role === 'HR' || user?.role === 'ADMIN') && (
            <button
              onClick={() => { setActiveNav('approvals'); navigate('/approvals'); }}
              className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
                activeNav === 'approvals' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Approvals
            </button>
          )}

          {(user?.role === 'HR' || user?.role === 'ADMIN') && (
            <button
              onClick={() => { setActiveNav('admin'); navigate('/admin/users'); }}
              className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
                activeNav === 'admin' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Admin
            </button>
          )}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 ml-64">
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">My Leave Requests</h1>
              <p className="text-sm text-gray-500">{filteredRequests.length} request{filteredRequests.length !== 1 ? 's' : ''}</p>
            </div>

            <div className="flex items-center gap-4">
              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
              >
                <option value="ALL">All Status</option>
                <option value="PENDING">Pending</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="CANCELLED">Cancelled</option>
              </select>

              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-3"
                >
                  <div className="w-9 h-9 rounded-full bg-red-100 flex items-center justify-center">
                    <span className="text-sm font-medium text-red-600">
                      {user?.email?.[0].toUpperCase() || 'U'}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {`${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'User'}
                    </div>
                    <div className="text-xs text-gray-500">{user?.role}</div>
                  </div>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="p-6">
          {filteredRequests.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No leave requests</h3>
              <p className="text-gray-500">
                {statusFilter === 'ALL'
                  ? 'You haven\'t made any leave requests yet.'
                  : `No ${statusFilter.toLowerCase()} requests found.`}
              </p>
              <button
                onClick={() => navigate('/leaves/new')}
                className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Create New Request
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRequests.map((request) => (
                <div key={request.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-medium text-gray-900">{request.category && typeof request.category === 'object' ? request.category.name : 'Leave'}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                      </div>

                      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Duration</p>
                          <p className="text-sm font-medium text-gray-900">{request.total_hours} hours</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Start Date</p>
                          <p className="text-sm font-medium text-gray-900">
                            {formatDate(request.start_date)}
                            {request.start_time && (
                              <span className="text-gray-600"> {formatTime(request.start_time)}</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">End Date</p>
                          <p className="text-sm font-medium text-gray-900">
                            {formatDate(request.end_date)}
                            {request.end_time && (
                              <span className="text-gray-600"> {formatTime(request.end_time)}</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Requested</p>
                          <p className="text-sm font-medium text-gray-900">
                            {new Date(request.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </p>
                        </div>
                      </div>

                      {request.reason && (
                        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Reason</p>
                          <p className="text-sm text-gray-700">{request.reason}</p>
                        </div>
                      )}

                      {request.approver_comment && (
                        <div className="mt-4 p-3 bg-green-50 rounded-lg">
                          <p className="text-xs text-green-500 uppercase tracking-wide mb-1">Approver Comment</p>
                          <p className="text-sm text-green-700">{request.approver_comment}</p>
                        </div>
                      )}

                      {request.rejection_reason && (
                        <div className="mt-4 p-3 bg-red-50 rounded-lg">
                          <p className="text-xs text-red-500 uppercase tracking-wide mb-1">Rejection Reason</p>
                          <p className="text-sm text-red-700">{request.rejection_reason}</p>
                        </div>
                      )}
                    </div>

                    {request.status === 'PENDING' && (
                      <div className="ml-6">
                        <button
                          onClick={() => handleCancel(request.id)}
                          className="px-4 py-2 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
