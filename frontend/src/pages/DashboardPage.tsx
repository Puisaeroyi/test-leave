import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { leavesApi } from '../api/leaves';
import type { LeaveRequest, LeaveBalance, PublicHoliday } from '../types';

// Team leave data from API
type TeamLeave = { id: string; member_id: string; start_date: string; end_date: string; category: string; is_full_day?: boolean; start_time: string | null; end_time: string | null; total_hours?: number };

// Discriminated union for dashboard events
type DashboardEvent =
  | { type: 'holiday'; data: PublicHoliday }
  | { type: 'myleave'; data: LeaveRequest }
  | { type: 'teamleave'; data: TeamLeave };

// Parse date string as local date to avoid timezone shift
function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day);
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeNav, setActiveNav] = useState('dashboard');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount] = useState(0);
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [leaveBalance, setLeaveBalance] = useState<LeaveBalance | null>(null);
  const [publicHolidays, setPublicHolidays] = useState<PublicHoliday[]>([]);
  const [teamCalendarData, setTeamCalendarData] = useState<{
    team_members: Array<{ id: string; name: string; color: string; is_current_user: boolean }>;
    leaves: TeamLeave[];
    holidays: Array<{ date: string; name: string }>;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [weekOffset, setWeekOffset] = useState(0);
  const [weekRange, setWeekRange] = useState<{ start: string; end: string }>({ start: '', end: '' });

  // Calculate week range based on offset
  const getWeekRange = (offset: number = 0) => {
    const now = new Date();
    const dayOfWeek = now.getDay();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - dayOfWeek + (offset * 7));
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    return { start: startOfWeek, end: endOfWeek };
  };

  // Update week range display when offset changes
  useEffect(() => {
    const { start: startOfWeek, end: endOfWeek } = getWeekRange(weekOffset);

    const formatDate = (date: Date) => {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${months[date.getMonth()]} ${date.getDate()}`;
    };

    setWeekRange({
      start: formatDate(startOfWeek),
      end: formatDate(endOfWeek),
    });
  }, [weekOffset]);

  const goToPreviousWeek = () => setWeekOffset(prev => prev - 1);
  const goToNextWeek = () => setWeekOffset(prev => prev + 1);
  const goToCurrentWeek = () => setWeekOffset(0);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentYear = new Date().getFullYear();

        // Fetch latest 3 leave requests
        const requests = await leavesApi.getLeaveRequests();
        setLeaveRequests(requests.slice(0, 3));

        // Fetch leave balance
        const balance = await leavesApi.getMyLeaveBalance(currentYear);
        setLeaveBalance(balance);

        // Fetch public holidays for current year
        const holidays = await leavesApi.getPublicHolidays({
          entity: user?.entity,
          location: user?.location,
          year: currentYear,
        });
        setPublicHolidays(holidays);

        // Fetch team calendar for selected week's month
        fetchTeamCalendarForWeek(weekOffset);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user]);

  // Fetch team calendar when week changes
  useEffect(() => {
    if (user) {
      fetchTeamCalendarForWeek(weekOffset);
    }
  }, [weekOffset, user]);

  // Helper to fetch team calendar for a specific week's month
  const fetchTeamCalendarForWeek = async (offset: number) => {
    try {
      const { start: startOfWeek } = getWeekRange(offset);
      const monthForWeek = startOfWeek.getMonth() + 1;
      const yearForWeek = startOfWeek.getFullYear();

      const calendarData = await leavesApi.getTeamCalendar({
        month: monthForWeek,
        year: yearForWeek,
      });
      setTeamCalendarData(calendarData);
    } catch (error) {
      console.error('Failed to fetch team calendar:', error);
    }
  };

  const getWeekNumber = (date: Date) => {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
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

  const getCategoryColor = (categoryName: string) => {
    const colors: Record<string, string> = {
      'Annual Leave': 'bg-blue-500',
      'Sick Leave': 'bg-red-500',
      'Personal Leave': 'bg-purple-500',
      'Maternity Leave': 'bg-pink-500',
      'Paternity Leave': 'bg-indigo-500',
      'Unpaid Leave': 'bg-gray-500',
    };
    return colors[categoryName] || 'bg-gray-500';
  };

  // Pie chart component
  const LeaveBalancePieChart = ({ balance }: { balance: LeaveBalance }) => {
    const total = balance.allocated_hours;
    const used = balance.used_hours;
    const remaining = balance.remaining_hours;
    const remainingPercentage = (remaining / total) * 100;

    return (
      <div className="flex items-center justify-center">
        <svg width="120" height="120" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#DC2626"
            strokeWidth="20"
            strokeDasharray={`${(used / total) * 251.2} 251.2`}
            transform="rotate(-90 50 50)"
          />
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="20"
            strokeDasharray={`${(remaining / total) * 251.2} 251.2`}
            strokeDashoffset={`-${(used / total) * 251.2}`}
            transform="rotate(-90 50 50)"
          />
          <text
            x="50"
            y="50"
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-sm font-semibold"
            fill="#1F2937"
          >
            {Math.round(remainingPercentage)}%
          </text>
        </svg>
      </div>
    );
  };

  const handleLogout = async () => {
    await logout();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-200 border-t-red-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex">
      {/* Left Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white shadow-md z-10 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <img src="/teampl.ico" alt="TeamPL" className="w-48 h-auto" />
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {/* New Request */}
          <button
            onClick={() => { setActiveNav('new-leave'); navigate('/leaves/new'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'new-leave'
                ? 'bg-red-50 text-red-600 font-medium'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Request
          </button>

          {/* Dashboard */}
          <button
            onClick={() => { setActiveNav('dashboard'); navigate('/'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'dashboard'
                ? 'bg-red-50 text-red-600 font-medium'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            Dashboard
          </button>

          {/* Team Calendar */}
          <button
            onClick={() => { setActiveNav('calendar'); navigate('/calendar'); }}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
              activeNav === 'calendar'
                ? 'bg-red-50 text-red-600 font-medium'
                : 'text-gray-700 hover:bg-gray-100'
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
                activeNav === 'approvals'
                  ? 'bg-red-50 text-red-600 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
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
                activeNav === 'admin'
                  ? 'bg-red-50 text-red-600 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
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

        {/* Bottom Section - Sign Out */}
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

      {/* Main Content Area */}
      <div className="flex-1 ml-64">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500">Welcome back, {user?.first_name || 'User'}!</p>
            </div>

            <div className="flex items-center gap-4">
            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900">Notifications</h3>
                  </div>
                  <div className="p-4 text-sm text-gray-500">
                    No new notifications
                  </div>
                </div>
              )}
            </div>

            {/* User Avatar */}
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
                  <div className="text-xs text-gray-500">
                    {user?.role} {user?.entity_name ? `• ${user.entity_name}` : ''}
                  </div>
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

        {/* Main Content */}
        <main className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left & Middle - Leave History */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Leave History</h2>
                    <button
                      onClick={() => navigate('/leaves')}
                      className="text-sm text-red-600 hover:text-red-700 font-medium"
                    >
                      View All
                    </button>
                  </div>
                </div>

                <div className="p-6">
                  {leaveRequests.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500">No leave requests yet</p>
                      <button
                        onClick={() => navigate('/leaves/new')}
                        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                      >
                        Create Leave Request
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-3">
                        {leaveRequests.map((request) => (
                          <div
                            key={request.id}
                            className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex items-center gap-4">
                              <div className={`w-3 h-3 rounded-full ${
                                request.category && typeof request.category === 'object'
                                  ? getCategoryColor(request.category.name)
                                  : 'bg-gray-500'
                              }`} />
                              <div>
                                <p className="font-medium text-gray-900">
                                  {request.category && typeof request.category === 'object'
                                    ? request.category.name
                                    : 'Leave'}
                                </p>
                                <p className="text-sm text-gray-500">
                                  {parseLocalDate(request.start_date).toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                  })}
                                  {request.start_date !== request.end_date && (
                                    <> - {parseLocalDate(request.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</>
                                  )}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              <span className="text-sm text-gray-600">{request.total_hours}h</span>
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                                {request.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>

                      <button
                        onClick={() => navigate('/leaves')}
                        className="w-full mt-4 py-2 text-sm text-gray-600 hover:text-gray-900 font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        Load More
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Leave Balance */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">Leave Balance</h2>
                  <p className="text-xs text-gray-500">{new Date().getFullYear()}</p>
                </div>

                <div className="p-6">
                  {leaveBalance ? (
                    <>
                      <LeaveBalancePieChart balance={leaveBalance} />

                      <div className="mt-4 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Total Hours</span>
                          <span className="font-semibold text-gray-900">{leaveBalance.allocated_hours}h</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Used Hours</span>
                          <span className="font-semibold text-red-600">{leaveBalance.used_hours}h</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Remaining</span>
                          <span className="font-semibold text-green-600">{leaveBalance.remaining_hours}h</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="text-gray-500 text-center py-4">No balance data available</p>
                  )}
                </div>
              </div>

              {/* Upcoming Events */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">Upcoming Events</h2>
                      <p className="text-xs text-gray-500">
                        Week-{getWeekNumber(getWeekRange(weekOffset).start).toString().padStart(2, '0')} ({weekRange.start} - {weekRange.end})
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={goToPreviousWeek}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Previous week"
                      >
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      <button
                        onClick={goToCurrentWeek}
                        className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Go to current week"
                      >
                        Today
                      </button>
                      <button
                        onClick={goToNextWeek}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Next week"
                      >
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  <div className="space-y-3">
                    {(() => {
                      // Get selected week range
                      const { start: startOfWeek, end: endOfWeek } = getWeekRange(weekOffset);

                      // Filter events for selected week
                      const filteredHolidays = publicHolidays.filter(holiday => {
                        const holidayDate = parseLocalDate(holiday.date);
                        return holidayDate >= startOfWeek && holidayDate <= endOfWeek;
                      });

                      const filteredMyLeaves = leaveRequests
                        .filter(req => req.status === 'APPROVED')
                        .filter(req => {
                          const reqDate = parseLocalDate(req.start_date);
                          return reqDate >= startOfWeek && reqDate <= endOfWeek;
                        });

                      const filteredTeamLeaves = (teamCalendarData?.leaves || [])
                        .filter(leave => {
                          const member = teamCalendarData?.team_members.find(m => m.id === leave.member_id);
                          if (!member || member.id === user?.id) return false;
                          const leaveStart = parseLocalDate(leave.start_date);
                          return leaveStart >= startOfWeek && leaveStart <= endOfWeek;
                        });

                      const allEvents: DashboardEvent[] = [
                        ...filteredHolidays.map(h => ({ type: 'holiday' as const, data: h })),
                        ...filteredMyLeaves.map(l => ({ type: 'myleave' as const, data: l })),
                        ...filteredTeamLeaves.map(l => ({ type: 'teamleave' as const, data: l }))
                      ].sort((a, b) => {
                        const aDate = a.type === 'holiday' ? parseLocalDate(a.data.date) : parseLocalDate(a.data.start_date);
                        const bDate = b.type === 'holiday' ? parseLocalDate(b.data.date) : parseLocalDate(b.data.start_date);
                        return aDate.getTime() - bDate.getTime();
                      });

                      if (allEvents.length === 0) {
                        return (
                          <p className="text-gray-500 text-center py-4 text-sm">
                            {`No events for Week-${getWeekNumber(getWeekRange(weekOffset).start).toString().padStart(2, '0')} (${weekRange.start} - ${weekRange.end})`}
                          </p>
                        );
                      }

                      return allEvents.map((event) => {
                        if (event.type === 'holiday') {
                          const holiday = event.data;
                          return (
                            <div key={`holiday-${holiday.id}`} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                              <div className="mt-0.5">
                                <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <p className="text-sm font-medium text-gray-900">{holiday.name}</p>
                                <p className="text-xs text-gray-500">
                                  {parseLocalDate(holiday.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                </p>
                              </div>
                              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">Holiday</span>
                            </div>
                          );
                        }

                        if (event.type === 'myleave') {
                          const req = event.data;
                          const startDate = parseLocalDate(req.start_date);
                          const endDate = parseLocalDate(req.end_date);
                          const isSameDay = req.start_date === req.end_date;

                          let dateRange: string;
                          if (isSameDay && req.start_time && req.end_time) {
                            // Same day with time range - add weekday
                            const weekday = startDate.toLocaleDateString('en-US', { weekday: 'short' });
                            const [startH, startM] = req.start_time.split(':').map(Number);
                            const [endH, endM] = req.end_time.split(':').map(Number);
                            const startTime = `${startH % 12 || 12}:${startM.toString().padStart(2, '0')} ${startH >= 12 ? 'PM' : 'AM'}`;
                            const endTime = `${endH % 12 || 12}:${endM.toString().padStart(2, '0')} ${endH >= 12 ? 'PM' : 'AM'}`;
                            dateRange = `${weekday} ${startTime} - ${endTime}`;
                          } else if (isSameDay) {
                            // Same day, full day - add weekday
                            dateRange = startDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                          } else {
                            // Date range - add weekday to start date
                            const startStr = startDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                            const endStr = endDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                            dateRange = `${startStr} - ${endStr}`;
                          }

                          return (
                            <div key={`myleave-${req.id}`} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                              <div className="mt-0.5">
                                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <p className="text-sm font-medium text-gray-900">My Leave</p>
                                <p className="text-xs text-gray-500">
                                  {req.category && typeof req.category === 'object' ? req.category.name : 'Leave'}
                                </p>
                              </div>
                              <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">{dateRange}</span>
                            </div>
                          );
                        }

                        // teamleave
                        const leave = event.data;
                        const member = teamCalendarData?.team_members.find(m => m.id === leave.member_id);
                        if (!member) return null;

                        const startDate = parseLocalDate(leave.start_date);
                        const endDate = parseLocalDate(leave.end_date);
                        const isSameDay = leave.start_date === leave.end_date;

                        let dateRange: string;
                        if (isSameDay && leave.start_time && leave.end_time) {
                          // Same day with time range - add weekday
                          const weekday = startDate.toLocaleDateString('en-US', { weekday: 'short' });
                          const [startH, startM] = leave.start_time.split(':').map(Number);
                          const [endH, endM] = leave.end_time.split(':').map(Number);
                          const startTime = `${startH % 12 || 12}:${startM.toString().padStart(2, '0')} ${startH >= 12 ? 'PM' : 'AM'}`;
                          const endTime = `${endH % 12 || 12}:${endM.toString().padStart(2, '0')} ${endH >= 12 ? 'PM' : 'AM'}`;
                          dateRange = `${weekday} ${startTime} - ${endTime}`;
                        } else if (isSameDay) {
                          // Same day, full day - weekday already included
                          dateRange = startDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                        } else {
                          // Date range - add weekday to start and end
                          const startStr = startDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                          const endStr = endDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                          dateRange = `${startStr} - ${endStr}`;
                        }

                        return (
                          <div key={`teamleave-${leave.id}`} className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                            <div className="mt-0.5">
                              <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                              </svg>
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">{member.name}</p>
                              <p className="text-xs text-gray-500">{leave.category}</p>
                            </div>
                            <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                              {dateRange}
                            </span>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
