import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { leavesApi } from '../api/leaves';
import type { LeaveCategory, LeaveRequest, LeaveBalance } from '../types';

export default function LeaveRequestPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeNav, setActiveNav] = useState('new-leave');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [categories, setCategories] = useState<LeaveCategory[]>([]);
  const [leaveBalance, setLeaveBalance] = useState<LeaveBalance | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Form state
  const [leaveType, setLeaveType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [shiftType, setShiftType] = useState<'FULL_DAY' | 'CUSTOM_HOURS'>('FULL_DAY');
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('17:00');
  const [reason, setReason] = useState('');
  const [attachment, setAttachment] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch categories and balance on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch categories
        const categoriesData = await leavesApi.getLeaveCategories();
        setCategories(categoriesData);
        if (categoriesData.length > 0) {
          setLeaveType(categoriesData[0].id);
        }

        // Fetch leave balance for current year
        const currentYear = new Date().getFullYear();
        const balanceData = await leavesApi.getMyLeaveBalance(currentYear);
        setLeaveBalance(balanceData);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    };
    fetchData();
  }, []);

  // Calculate hours to be deducted
  const calculateHoursToDeduct = (): number => {
    if (!startDate || !endDate) return 0;

    const start = new Date(startDate);
    const end = new Date(endDate);
    const daysDiff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

    // If single day and custom hours
    if (daysDiff === 1 && shiftType === 'CUSTOM_HOURS' && startTime && endTime) {
      const [startH, startM] = startTime.split(':').map(Number);
      const [endH, endM] = endTime.split(':').map(Number);
      const startMinutes = startH * 60 + startM;
      const endMinutes = endH * 60 + endM;
      return Math.max(0, (endMinutes - startMinutes) / 60);
    }

    // Default: 8 hours per day for full day leave
    return daysDiff * 8;
  };

  const hoursToDeduct = calculateHoursToDeduct();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    const newErrors: Record<string, string> = {};

    if (!leaveType) newErrors.leaveType = 'Please select a leave type';
    if (!startDate) newErrors.startDate = 'Please select a start date';
    if (!endDate) newErrors.endDate = 'Please select an end date';
    if (new Date(startDate) > new Date(endDate)) {
      newErrors.endDate = 'End date must be after start date';
    }
    // Only validate shift type and times if it's a single day leave
    if (startDate === endDate) {
      if (shiftType === 'CUSTOM_HOURS' && (!startTime || !endTime)) {
        newErrors.time = 'Please specify start and end time';
      }
    }
    if (!reason.trim()) newErrors.reason = 'Please provide a reason';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('leave_category', leaveType);
      formData.append('start_date', startDate);
      formData.append('end_date', endDate);
      // Only include shift_type and times for single day
      if (startDate === endDate) {
        formData.append('shift_type', shiftType);
        if (shiftType === 'CUSTOM_HOURS') {
          formData.append('start_time', startTime);
          formData.append('end_time', endTime);
        }
      }
      formData.append('reason', reason);
      if (attachment) {
        formData.append('attachment', attachment);
      }

      await leavesApi.createLeaveRequest(formData);
      navigate('/');
    } catch (err: any) {
      console.error('Leave request error:', err);
      if (err.response?.data) {
        const errorMsg = typeof err.response.data === 'string'
          ? err.response.data
          : err.response.data.detail || JSON.stringify(err.response.data);
        setErrors({ form: errorMsg });
      } else {
        setErrors({ form: 'Unable to create leave request. Please try again.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const getCategoryName = (categoryId: string) => {
    const cat = categories.find(c => c.id === categoryId);
    return cat?.name || 'Leave';
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
              <h1 className="text-xl font-semibold text-gray-900">New Leave Request</h1>
              <p className="text-sm text-gray-500">Create a new leave request</p>
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
            {/* Left - Form */}
            <div className="lg:col-span-2">
              <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 space-y-6">
                {/* Leave Type */}
                <div>
                  <label htmlFor="leaveType" className="block text-sm font-semibold text-gray-700 mb-2">
                    Leave Type *
                  </label>
                  <select
                    id="leaveType"
                    value={leaveType}
                    onChange={(e) => {
                      setLeaveType(e.target.value);
                      if (errors.leaveType) setErrors({ ...errors, leaveType: '' });
                    }}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    required
                  >
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                  {errors.leaveType && (
                    <p className="mt-1 text-sm text-red-600">{errors.leaveType}</p>
                  )}
                </div>

                {/* Date Range */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="startDate" className="block text-sm font-semibold text-gray-700 mb-2">
                      Start Date *
                    </label>
                    <input
                      id="startDate"
                      type="date"
                      value={startDate}
                      onChange={(e) => {
                        setStartDate(e.target.value);
                        if (errors.startDate) setErrors({ ...errors, startDate: '' });
                      }}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      required
                    />
                    {errors.startDate && (
                      <p className="mt-1 text-sm text-red-600">{errors.startDate}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="endDate" className="block text-sm font-semibold text-gray-700 mb-2">
                      End Date *
                    </label>
                    <input
                      id="endDate"
                      type="date"
                      value={endDate}
                      onChange={(e) => {
                        setEndDate(e.target.value);
                        if (errors.endDate) setErrors({ ...errors, endDate: '' });
                      }}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      required
                    />
                    {errors.endDate && (
                      <p className="mt-1 text-sm text-red-600">{errors.endDate}</p>
                    )}
                  </div>
                </div>

                {/* Shift Type - Only show for single day leave */}
                {startDate && endDate && startDate === endDate && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Shift Type *
                    </label>
                    <div className="flex gap-4">
                      <label className={`flex items-center px-4 py-3 border rounded-lg cursor-pointer transition-colors ${
                        shiftType === 'FULL_DAY'
                          ? 'bg-red-50 border-red-500'
                          : 'border-gray-300 hover:bg-gray-50'
                      }`}>
                        <input
                          type="radio"
                          name="shiftType"
                          value="FULL_DAY"
                          checked={shiftType === 'FULL_DAY'}
                          onChange={(e) => {
                            setShiftType('FULL_DAY');
                            if (errors.time) setErrors({ ...errors, time: '' });
                          }}
                          className="sr-only"
                        />
                        <span className="text-sm font-medium">Full Day</span>
                      </label>

                      <label className={`flex items-center px-4 py-3 border rounded-lg cursor-pointer transition-colors ${
                        shiftType === 'CUSTOM_HOURS'
                          ? 'bg-red-50 border-red-500'
                          : 'border-gray-300 hover:bg-gray-50'
                      }`}>
                        <input
                          type="radio"
                          name="shiftType"
                          value="CUSTOM_HOURS"
                          checked={shiftType === 'CUSTOM_HOURS'}
                          onChange={(e) => {
                            setShiftType('CUSTOM_HOURS');
                          }}
                          className="sr-only"
                        />
                        <span className="text-sm font-medium">Custom Hours</span>
                      </label>
                    </div>
                    {errors.time && (
                      <p className="mt-1 text-sm text-red-600">{errors.time}</p>
                    )}
                  </div>
                )}

                {/* Custom Hours - Only show for single day leave with Custom Hours */}
                {startDate && endDate && startDate === endDate && shiftType === 'CUSTOM_HOURS' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="startTime" className="block text-sm font-semibold text-gray-700 mb-2">
                        Start Time
                      </label>
                      <input
                        id="startTime"
                        type="time"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label htmlFor="endTime" className="block text-sm font-semibold text-gray-700 mb-2">
                        End Time
                      </label>
                      <input
                        id="endTime"
                        type="time"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                )}

                {/* Reason */}
                <div>
                  <label htmlFor="reason" className="block text-sm font-semibold text-gray-700 mb-2">
                    Reason *
                  </label>
                  <textarea
                    id="reason"
                    value={reason}
                    onChange={(e) => {
                      setReason(e.target.value);
                      if (errors.reason) setErrors({ ...errors, reason: '' });
                    }}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
                    placeholder="Provide a reason for your leave request..."
                    required
                  />
                  {errors.reason && (
                    <p className="mt-1 text-sm text-red-600">{errors.reason}</p>
                  )}
                </div>

                {/* Attachment */}
                <div>
                  <label htmlFor="attachment" className="block text-sm font-semibold text-gray-700 mb-2">
                    Attachment
                  </label>
                  <input
                    id="attachment"
                    type="file"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setAttachment(file);
                      }
                    }}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-50 file:text-red-700 hover:file:bg-red-100"
                  />
                  {attachment && (
                    <p className="mt-2 text-sm text-gray-600">
                      Selected: {attachment.name}
                    </p>
                  )}
                </div>

                {/* Hours Deduction Info */}
                {hoursToDeduct > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
                    <p className="text-sm text-blue-800">
                      Your leave balance will be deducted by <strong>{hoursToDeduct.toFixed(1)} hours</strong>
                    </p>
                  </div>
                )}

                {/* Form Error */}
                {errors.form && (
                  <div className="bg-red-50 px-4 py-3 text-red-700 text-sm rounded-lg">
                    <p>{errors.form}</p>
                  </div>
                )}

                {/* Submit Button */}
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => navigate('/')}
                    className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? 'Submitting...' : 'Submit Request'}
                  </button>
                </div>
              </div>
            </form>
            </div>

            {/* Right - Leave Balance */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Leave Balance</h2>
                {leaveBalance ? (
                  <div className="space-y-4">
                    {/* Pie Chart */}
                    <div className="flex justify-center">
                      <svg width="140" height="140" viewBox="0 0 100 100">
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          fill="none"
                          stroke="#DC2626"
                          strokeWidth="20"
                          strokeDasharray={`${(leaveBalance.used_hours / leaveBalance.allocated_hours) * 251.2} 251.2`}
                          transform="rotate(-90 50 50)"
                        />
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          fill="none"
                          stroke="#E5E7EB"
                          strokeWidth="20"
                          strokeDasharray={`${(leaveBalance.remaining_hours / leaveBalance.allocated_hours) * 251.2} 251.2`}
                          strokeDashoffset={`-${(leaveBalance.used_hours / leaveBalance.allocated_hours) * 251.2}`}
                          transform="rotate(-90 50 50)"
                        />
                        <text
                          x="50"
                          y="50"
                          textAnchor="middle"
                          dominantBaseline="middle"
                          className="text-base font-bold"
                          fill="#1F2937"
                        >
                          {Math.round((leaveBalance.remaining_hours / leaveBalance.allocated_hours) * 100)}%
                        </text>
                      </svg>
                    </div>

                    {/* Details */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Allocated</span>
                        <span className="text-sm font-semibold text-gray-900">{leaveBalance.allocated_hours} hrs</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Used</span>
                        <span className="text-sm font-semibold text-red-600">{leaveBalance.used_hours} hrs</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Remaining</span>
                        <span className="text-sm font-semibold text-green-600">{leaveBalance.remaining_hours} hrs</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="animate-pulse text-gray-400">Loading balance...</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
