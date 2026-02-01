import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { leavesApi } from '../api/leaves';

/**
 * BusinessTripPage - Form for registering business trips
 * Key differences from leave request:
 * - No approval workflow (no status, no approval fields)
 * - Does NOT deduct from leave balance
 * - Requires dates + destination (city, country) + optional note
 */
export default function BusinessTripPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Form state
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Calculate trip days (simple client-side estimate)
  const calculateDays = (): number => {
    if (!startDate || !endDate) return 0;
    const start = new Date(startDate);
    const end = new Date(endDate);
    let days = 0;
    const current = new Date(start);
    while (current <= end) {
      if (current.getDay() !== 0 && current.getDay() !== 6) {
        days++;
      }
      current.setDate(current.getDate() + 1);
    }
    return days;
  };

  const tripDays = calculateDays();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSuccessMessage('');

    const newErrors: Record<string, string> = {};

    if (!startDate) newErrors.startDate = 'Please select departure date';
    if (!endDate) newErrors.endDate = 'Please select return date';
    if (!city.trim()) newErrors.city = 'City is required';
    if (!country.trim()) newErrors.country = 'Country is required';
    if (city.trim().length < 2) newErrors.city = 'City must be at least 2 characters';
    if (country.trim().length < 2) newErrors.country = 'Country must be at least 2 characters';
    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      newErrors.endDate = 'Return date must be on or after departure date';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      await leavesApi.createBusinessTrip({
        start_date: startDate,
        end_date: endDate,
        city: city.trim(),
        country: country.trim(),
        note: note.trim(),
      });
      setSuccessMessage('Business trip registered successfully!');
      setTimeout(() => navigate('/'), 1500);
    } catch (err: any) {
      if (err.response?.data?.error) {
        setErrors({ form: err.response.data.error });
      } else if (err.response?.data?.city) {
        setErrors({ city: err.response.data.city[0] });
      } else if (err.response?.data?.country) {
        setErrors({ country: err.response.data.country[0] });
      } else {
        setErrors({ form: 'Failed to register business trip. Please try again.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white shadow-md z-10 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <img src="/teampl.ico" alt="TeamPL" className="w-48 h-auto" />
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <button
            onClick={() => navigate('/business-trips/new')}
            className="w-full flex items-center px-4 py-3 rounded-lg bg-teal-50 text-teal-600 font-medium"
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            Business Trip
          </button>
          <button
            onClick={() => navigate('/leaves/new')}
            className="w-full flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Leave
          </button>
          <button
            onClick={() => navigate('/')}
            className="w-full flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" />
            </svg>
            Dashboard
          </button>
          <button
            onClick={() => navigate('/calendar')}
            className="w-full flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
          >
            <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Calendar
          </button>
        </nav>
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={() => logout()}
            className="w-full flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
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
          <h1 className="text-xl font-semibold text-gray-900">Register Business Trip</h1>
          <p className="text-sm text-gray-500">Business trips have no approval workflow and do not affect leave balance</p>
        </header>

        <main className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Form */}
            <div className="lg:col-span-2">
              <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                {successMessage && (
                  <div className="mb-6 bg-green-50 border border-green-200 rounded-lg px-4 py-3">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <p className="text-green-800 font-medium">{successMessage}</p>
                    </div>
                  </div>
                )}

                <div className="space-y-6">
                  {/* Date Range */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Departure Date *
                      </label>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                        required
                      />
                      {errors.startDate && <p className="mt-1 text-sm text-red-600">{errors.startDate}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Return Date *
                      </label>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                        required
                      />
                      {errors.endDate && <p className="mt-1 text-sm text-red-600">{errors.endDate}</p>}
                    </div>
                  </div>

                  {/* Destination - City and Country */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        City *
                      </label>
                      <input
                        type="text"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                        placeholder="e.g., Tokyo"
                        required
                      />
                      {errors.city && <p className="mt-1 text-sm text-red-600">{errors.city}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Country *
                      </label>
                      <input
                        type="text"
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                        placeholder="e.g., Japan"
                        required
                      />
                      {errors.country && <p className="mt-1 text-sm text-red-600">{errors.country}</p>}
                    </div>
                  </div>

                  {/* Note (Optional) */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Note <span className="font-normal text-gray-500">(optional)</span>
                    </label>
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      rows={3}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
                      placeholder="e.g., Client meeting, conference attendance, project onsite work..."
                    />
                  </div>

                  {/* Trip Duration Info */}
                  {tripDays > 0 && (
                    <div className="bg-teal-50 border border-teal-200 rounded-lg px-4 py-3">
                      <p className="text-sm text-teal-800">
                        Trip duration: <strong>{tripDays} working day{tripDays > 1 ? 's' : ''}</strong>
                      </p>
                    </div>
                  )}

                  {/* Form Error */}
                  {errors.form && (
                    <div className="bg-red-50 px-4 py-3 text-red-700 text-sm rounded-lg">
                      {errors.form}
                    </div>
                  )}

                  {/* Buttons */}
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => navigate('/')}
                      className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex-1 bg-teal-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-teal-700 disabled:opacity-50"
                    >
                      {isLoading ? 'Registering...' : 'Register Trip'}
                    </button>
                  </div>
                </div>
              </form>
            </div>

            {/* Info Sidebar */}
            <div className="lg:col-span-1">
              {/* About Business Trips Card */}
              <div className="bg-teal-50 rounded-lg p-6 border border-teal-200">
                <h3 className="text-lg font-semibold text-teal-800 mb-3">About Business Trips</h3>
                <ul className="text-sm text-teal-700 space-y-2">
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    No approval workflow needed
                  </li>
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Does NOT deduct from leave balance
                  </li>
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Visible on team calendar
                  </li>
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Track city and country for each trip
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
