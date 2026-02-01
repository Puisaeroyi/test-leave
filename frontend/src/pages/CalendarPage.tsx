import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { leavesApi } from '../api/leaves';

interface TeamMember {
  id: string;
  name: string;
  color: string;
  is_current_user: boolean;
}

interface Leave {
  id: string;
  member_id: string;
  start_date: string;
  end_date: string;
  is_full_day: boolean;
  start_time: string | null;
  end_time: string | null;
  category: string;
  total_hours: number;
}

interface Holiday {
  date: string;
  name: string;
}

interface BusinessTripCalendar {
  id: string;
  member_id: string;
  start_date: string;
  end_date: string;
  total_hours: number;
  reason: string;
}

interface CalendarData {
  month: number;
  year: number;
  team_members: TeamMember[];
  leaves: Leave[];
  business_trips?: BusinessTripCalendar[];
  holidays: Holiday[];
}

// Format time to AM/PM
function formatTime(time: string) {
  const [hours, minutes] = time.split(':').map(Number);
  const period = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
}

// Get short name from full name
function getShortName(name: string) {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 3).toUpperCase();
  return parts[parts.length - 1].substring(0, 3).toUpperCase();
}

// Parse date string as local date (no timezone conversion)
function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day);
}

// Format Date to local date string (no timezone conversion)
function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Get Tailwind color classes from hex
function getColorClasses(hexColor: string) {
  const colorMap: { [key: string]: { bg: string; dot: string; text: string } } = {
    '#3B82F6': { bg: 'bg-blue-500', dot: 'bg-blue-400', text: 'text-blue-400' },
    '#10B981': { bg: 'bg-green-500', dot: 'bg-green-400', text: 'text-green-400' },
    '#8B5CF6': { bg: 'bg-purple-500', dot: 'bg-purple-400', text: 'text-purple-400' },
    '#F97316': { bg: 'bg-orange-500', dot: 'bg-orange-400', text: 'text-orange-400' },
    '#EC4899': { bg: 'bg-pink-500', dot: 'bg-pink-400', text: 'text-pink-400' },
    '#14B8A6': { bg: 'bg-teal-500', dot: 'bg-teal-400', text: 'text-teal-400' },
  };

  return colorMap[hexColor] || colorMap['#3B82F6'];
}

// Business trips always use teal color
const BUSINESS_TRIP_COLOR = { bg: 'bg-teal-500', dot: 'bg-teal-400', text: 'text-teal-400' };

export default function CalendarPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeNav, setActiveNav] = useState('calendar');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [calendarData, setCalendarData] = useState<CalendarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  useEffect(() => {
    loadCalendarData();
    loadNotifications();
  }, [year, month, selectedMembers]);

  async function loadCalendarData() {
    try {
      setLoading(true);
      setError(null);
      const data = await leavesApi.getTeamCalendar({ month: month + 1, year });
      setCalendarData(data as any);

      // Initialize selected members if empty
      if (selectedMembers.length === 0 && data.team_members && data.team_members.length > 0) {
        setSelectedMembers(data.team_members.map((m: any) => m.id));
      }
    } catch (err) {
      setError('Failed to load calendar data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function loadNotifications() {
    try {
      // This would call a notifications API - placeholder for now
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }

  const handleLogout = async () => {
    await logout();
  };

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startingDayOfWeek = new Date(year, month, 1).getDay();

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Generate weeks for the calendar
  const weeks: (Date | null)[][] = [];
  let currentWeek: (Date | null)[] = [];

  for (let i = 0; i < startingDayOfWeek; i++) {
    currentWeek.push(null);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    currentWeek.push(new Date(year, month, day));
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }

  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push(null);
    }
    weeks.push(currentWeek);
  }

  const goToPrevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const goToNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  const toggleMember = (memberId: string) => {
    setSelectedMembers(prev =>
      prev.includes(memberId)
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    );
  };

  const isToday = (date: Date | null) => {
    if (!date) return false;
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
  };

  // Get partial day leaves for a specific date
  const getPartialDayLeaves = (date: Date) => {
    if (!calendarData) return [];
    const dateStr = formatLocalDate(date);
    return calendarData.leaves.filter(leave => {
      if (!selectedMembers.includes(leave.member_id)) return false;
      if (leave.is_full_day) return false;
      return leave.start_date === dateStr;
    });
  };

  // Get multi-day leaves that overlap with a week
  const getMultiDayLeavesForWeek = (week: (Date | null)[]) => {
    if (!calendarData) return [];
    const validDates = week.filter((d): d is Date => d !== null);
    if (validDates.length === 0) return [];

    const weekStart = validDates[0];
    const weekEnd = validDates[validDates.length - 1];

    return calendarData.leaves.filter(leave => {
      if (!selectedMembers.includes(leave.member_id)) return false;
      if (!leave.is_full_day) return false;
      const leaveStart = parseLocalDate(leave.start_date);
      const leaveEnd = parseLocalDate(leave.end_date);
      return leaveStart <= weekEnd && leaveEnd >= weekStart;
    });
  };

  // Get business trips that overlap with a week
  const getBusinessTripsForWeek = (week: (Date | null)[]) => {
    if (!calendarData?.business_trips) return [];
    const validDates = week.filter((d): d is Date => d !== null);
    if (validDates.length === 0) return [];

    const weekStart = validDates[0];
    const weekEnd = validDates[validDates.length - 1];

    return calendarData.business_trips.filter(trip => {
      if (!selectedMembers.includes(trip.member_id)) return false;
      const tripStart = parseLocalDate(trip.start_date);
      const tripEnd = parseLocalDate(trip.end_date);
      return tripStart <= weekEnd && tripEnd >= weekStart;
    });
  };

  // Calculate bar position for multi-day leave
  const getLeaveBarStyle = (leave: Leave, week: (Date | null)[]) => {
    const leaveStart = parseLocalDate(leave.start_date);
    const leaveEnd = parseLocalDate(leave.end_date);

    let startCol = 0;
    let endCol = 6;

    for (let i = 0; i < 7; i++) {
      const date = week[i];
      if (date) {
        const dateTime = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
        const leaveStartTime = new Date(leaveStart.getFullYear(), leaveStart.getMonth(), leaveStart.getDate()).getTime();
        const leaveEndTime = new Date(leaveEnd.getFullYear(), leaveEnd.getMonth(), leaveEnd.getDate()).getTime();

        if (dateTime === leaveStartTime) {
          startCol = i;
        }
        if (dateTime <= leaveEndTime) {
          endCol = i;
        }
      }
    }

    // Clamp to valid columns with dates
    const firstValidCol = week.findIndex(d => d !== null);
    const lastValidCol = week.reduce((last, d, i) => d !== null ? i : last, 0);

    if (startCol < firstValidCol) startCol = firstValidCol;
    if (endCol > lastValidCol) endCol = lastValidCol;

    const left = `${(startCol / 7) * 100}%`;
    const width = `${((endCol - startCol + 1) / 7) * 100}%`;

    return { left, width };
  };

  // Calculate bar position for business trip
  const getBusinessTripBarStyle = (trip: BusinessTripCalendar, week: (Date | null)[]) => {
    const tripStart = parseLocalDate(trip.start_date);
    const tripEnd = parseLocalDate(trip.end_date);

    let startCol = 0;
    let endCol = 6;

    for (let i = 0; i < 7; i++) {
      const date = week[i];
      if (date) {
        const dateTime = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
        const tripStartTime = new Date(tripStart.getFullYear(), tripStart.getMonth(), tripStart.getDate()).getTime();
        const tripEndTime = new Date(tripEnd.getFullYear(), tripEnd.getMonth(), tripEnd.getDate()).getTime();

        if (dateTime === tripStartTime) {
          startCol = i;
        }
        if (dateTime <= tripEndTime) {
          endCol = i;
        }
      }
    }

    // Clamp to valid columns with dates
    const firstValidCol = week.findIndex(d => d !== null);
    const lastValidCol = week.reduce((last, d, i) => d !== null ? i : last, 0);

    if (startCol < firstValidCol) startCol = firstValidCol;
    if (endCol > lastValidCol) endCol = lastValidCol;

    const left = `${(startCol / 7) * 100}%`;
    const width = `${((endCol - startCol + 1) / 7) * 100}%`;

    return { left, width };
  };

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
              <h1 className="text-xl font-semibold text-gray-900">Team Calendar</h1>
              <p className="text-sm text-gray-500">View team leave schedules</p>
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
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-gray-500">Loading calendar...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-red-500">{error}</div>
            </div>
          ) : !calendarData ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-gray-500">No data available</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
              {/* Calendar */}
              <div className="xl:col-span-4">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-gray-800">Team Calendar</h2>
                    <div className="flex items-center gap-4">
                      <button onClick={goToPrevMonth} className="w-10 h-10 flex items-center justify-center hover:bg-gray-100 rounded-lg transition-colors">
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      <span className="text-lg font-semibold text-gray-800 min-w-[160px] text-center">
                        {monthNames[month]} {year}
                      </span>
                      <button onClick={goToNextMonth} className="w-10 h-10 flex items-center justify-center hover:bg-gray-100 rounded-lg transition-colors">
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Day Headers */}
                  <div className="grid grid-cols-7 gap-1 mb-2">
                    {dayNames.map(day => (
                      <div key={day} className="text-center text-sm font-semibold text-gray-500 py-2">
                        {day}
                      </div>
                    ))}
                  </div>

                  {/* Calendar Weeks */}
                  <div className="space-y-1">
                    {weeks.map((week, weekIndex) => {
                      const multiDayLeaves = getMultiDayLeavesForWeek(week);
                      const businessTrips = getBusinessTripsForWeek(week);

                      return (
                        <div key={weekIndex} className="relative">
                          {/* Date cells */}
                          <div className="grid grid-cols-7 gap-1">
                            {week.map((date, dayIndex) => {
                              const partialLeaves = date ? getPartialDayLeaves(date) : [];

                              return (
                                <div
                                  key={dayIndex}
                                  className={`bg-gray-50 border border-gray-200 rounded p-2 min-h-[120px] ${
                                    date === null ? 'opacity-30' : ''
                                  } ${isToday(date) ? 'ring-2 ring-red-400' : ''}`}
                                >
                                  {date && (
                                    <>
                                      <div className={`text-sm font-medium mb-2 ${isToday(date) ? 'text-red-500' : 'text-gray-700'}`}>
                                        {date.getDate()}
                                      </div>
                                      {/* Partial day leaves - bullet + time */}
                                      <div className="space-y-1 mt-6">
                                        {partialLeaves.map((leave) => {
                                          const member = calendarData.team_members.find(m => m.id === leave.member_id);
                                          const color = member ? getColorClasses(member.color) : getColorClasses('#3B82F6');
                                          return (
                                            <div key={leave.id} className="flex items-center gap-1.5 text-xs">
                                              <div className={`w-2 h-2 rounded-full ${color.dot} flex-shrink-0`}></div>
                                              <span className={`${color.text} truncate`}>
                                                {leave.start_time && formatTime(leave.start_time)} - {leave.end_time && formatTime(leave.end_time)} {member && getShortName(member.name)}
                                              </span>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    </>
                                  )}
                                </div>
                              );
                            })}
                          </div>

                          {/* Multi-day leave bars overlay */}
                          <div className="absolute inset-x-0 top-8 pointer-events-none px-0.5">
                            <div className="relative">
                              {multiDayLeaves.map((leave, leaveIndex) => {
                                const { left, width } = getLeaveBarStyle(leave, week);
                                const member = calendarData.team_members.find(m => m.id === leave.member_id);
                                const color = member ? getColorClasses(member.color) : getColorClasses('#3B82F6');

                                return (
                                  <div
                                    key={`${leave.id}-${weekIndex}`}
                                    className={`absolute h-5 ${color.bg} rounded flex items-center px-2 shadow-sm`}
                                    style={{
                                      left,
                                      width,
                                      top: `${leaveIndex * 22}px`,
                                    }}
                                    title={`${member?.name} - ${leave.category}`}
                                  >
                                    <span className="text-xs text-white font-medium truncate">
                                      {member && getShortName(member.name)}'s Leave
                                    </span>
                                  </div>
                                );
                              })}
                              {/* Business trip bars overlay */}
                              {businessTrips.map((trip, tripIndex) => {
                                const { left, width } = getBusinessTripBarStyle(trip, week);
                                const member = calendarData.team_members.find(m => m.id === trip.member_id);
                                const barIndex = multiDayLeaves.length + tripIndex;

                                return (
                                  <div
                                    key={`${trip.id}-${weekIndex}`}
                                    className={`absolute h-5 ${BUSINESS_TRIP_COLOR.bg} rounded flex items-center px-2 shadow-sm`}
                                    style={{
                                      left,
                                      width,
                                      top: `${barIndex * 22}px`,
                                    }}
                                    title={`${member?.name} - ${trip.reason}`}
                                  >
                                    <span className="text-xs text-white font-medium truncate">
                                      {member && getShortName(member.name)}'s Trip
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* My Team Sidebar */}
              <div className="xl:col-span-1">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-lg font-bold text-gray-800 mb-4">My Team</h2>
                  <p className="text-xs text-gray-500 mb-4">Click to show/hide on calendar</p>

                  <div className="space-y-3">
                    {calendarData.team_members.map((member) => {
                      const color = getColorClasses(member.color);
                      const isSelected = selectedMembers.includes(member.id);

                      return (
                        <button
                          key={member.id}
                          onClick={() => toggleMember(member.id)}
                          className={`w-full bg-gray-50 border border-gray-200 rounded p-3 flex items-center gap-3 transition-opacity ${
                            isSelected ? 'opacity-100' : 'opacity-40'
                          }`}
                        >
                          <div className={`w-4 h-4 rounded-full ${color.bg} flex-shrink-0`}></div>
                          <div className="text-left flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-800 truncate">
                              {member.name}
                              {member.is_current_user && <span className="text-xs text-red-500 ml-1">(You)</span>}
                            </p>
                          </div>
                          <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 ${
                            isSelected ? 'bg-red-500' : 'bg-gray-200'
                          }`}>
                            {isSelected && (
                              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Legend */}
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Legend</h3>
                    <div className="space-y-2 text-xs text-gray-600">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-400"></div>
                        <span>Partial day (shows time)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-4 rounded bg-red-500"></div>
                        <span>Multi-day leave</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-4 rounded bg-teal-500"></div>
                        <span>Business trip</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded ring-2 ring-red-400"></div>
                        <span>Today</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
