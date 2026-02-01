import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import organizationsApi, { type Entity, type Location, type Department } from '../../api/organizations';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [entityId, setEntityId] = useState('');
  const [locationId, setLocationId] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Organization data
  const [entities, setEntities] = useState<Entity[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isLoadingOrgs, setIsLoadingOrgs] = useState(true);

  const { register } = useAuth();
  const navigate = useNavigate();

  // Load entities on mount
  useEffect(() => {
    const loadEntities = async () => {
      try {
        const data = await organizationsApi.getEntities();
        setEntities(data.filter((e) => e.is_active));
      } catch (err) {
        console.error('Failed to load entities:', err);
      } finally {
        setIsLoadingOrgs(false);
      }
    };
    loadEntities();
  }, []);

  // Load locations when entity changes
  useEffect(() => {
    if (!entityId) {
      setLocations([]);
      setDepartments([]);
      setLocationId('');
      setDepartmentId('');
      return;
    }

    const loadLocations = async () => {
      try {
        const locsData = await organizationsApi.getLocations(entityId);
        setLocations(locsData.filter((l) => l.is_active));
        setLocationId('');
        setDepartmentId('');
      } catch (err) {
        console.error('Failed to load locations:', err);
      }
    };
    loadLocations();
  }, [entityId]);

  // Load departments when location changes
  useEffect(() => {
    if (!locationId) {
      setDepartments([]);
      setDepartmentId('');
      return;
    }

    const loadDepartments = async () => {
      try {
        const deptsData = await organizationsApi.getDepartments(entityId, locationId);
        setDepartments(deptsData.filter((d) => d.is_active));
        setDepartmentId('');
      } catch (err) {
        console.error('Failed to load departments:', err);
      }
    };
    loadDepartments();
  }, [locationId, entityId]);

  const validateForm = (): boolean => {
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }

    if (!entityId || !locationId || !departmentId) {
      setError('Please select your organization, location, and department');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await register({
        email,
        password,
        password_confirm: confirmPassword,
        first_name: firstName,
        last_name: lastName,
        entity: entityId,
        location: locationId,
        department: departmentId,
      });

      // Redirect to dashboard after successful registration
      navigate('/', { replace: true });
    } catch (err: any) {
      console.error('Registration error:', err);
      if (err.response?.data) {
        const data = err.response.data;
        const errorMsg =
          typeof data === 'string'
            ? data
            : data.error ||
              data.email?.[0] ||
              data.entity?.[0] ||
              data.location?.[0] ||
              data.department?.[0] ||
              data.detail ||
              'Registration failed';
        setError(errorMsg);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Unable to connect to server. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center clay-bg px-4 py-8">
      <div className="max-w-md w-full">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="clay-avatar inline-flex items-center justify-center w-20 h-20 mb-5">
            <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Create Account</h1>
          <p className="text-gray-500">Sign up to get started with leave management</p>
        </div>

        {/* Register Card */}
        <div className="clay-card p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name Fields - Row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-semibold text-gray-700 mb-2">
                  First Name
                </label>
                <input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700 placeholder-gray-400"
                  placeholder="First name"
                  autoComplete="given-name"
                />
              </div>
              <div>
                <label htmlFor="lastName" className="block text-sm font-semibold text-gray-700 mb-2">
                  Last Name
                </label>
                <input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700 placeholder-gray-400"
                  placeholder="Last name"
                  autoComplete="family-name"
                />
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                Email <span className="text-red-500">*</span>
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="clay-input w-full px-4 py-3 text-gray-700 placeholder-gray-400"
                placeholder="Enter your email"
                autoComplete="email"
                required
              />
            </div>

            {/* Password Fields - Row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                  Password <span className="text-red-500">*</span>
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700 placeholder-gray-400"
                  placeholder="Password"
                  autoComplete="new-password"
                  required
                />
              </div>
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-700 mb-2">
                  Confirm <span className="text-red-500">*</span>
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700 placeholder-gray-400"
                  placeholder="Confirm"
                  autoComplete="new-password"
                  required
                />
              </div>
            </div>

            {/* Organization Section */}
            <div className="border-t pt-4 mt-4">
              <p className="text-sm font-semibold text-gray-700 mb-3">Organization Details</p>

              {/* Entity Dropdown */}
              <div className="mb-3">
                <label htmlFor="entity" className="block text-sm font-medium text-gray-700 mb-2">
                  Company <span className="text-red-500">*</span>
                </label>
                <select
                  id="entity"
                  value={entityId}
                  onChange={(e) => setEntityId(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700"
                  required
                  disabled={isLoadingOrgs}
                >
                  <option value="">Select company</option>
                  {entities.map((entity) => (
                    <option key={entity.id} value={entity.id}>
                      {entity.entity_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Location Dropdown */}
              <div className="mb-3">
                <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                  Location <span className="text-red-500">*</span>
                </label>
                <select
                  id="location"
                  value={locationId}
                  onChange={(e) => setLocationId(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700"
                  required
                  disabled={!entityId}
                >
                  <option value="">{entityId ? 'Select location' : 'Select company first'}</option>
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.location_name} ({loc.city})
                    </option>
                  ))}
                </select>
              </div>

              {/* Department Dropdown */}
              <div>
                <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-2">
                  Department <span className="text-red-500">*</span>
                </label>
                <select
                  id="department"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value)}
                  className="clay-input w-full px-4 py-3 text-gray-700"
                  required
                  disabled={!locationId}
                >
                  <option value="">{locationId ? 'Select department' : 'Select location first'}</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.department_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="clay-card-inset bg-red-50 px-4 py-3 text-red-700 text-sm">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || isLoadingOrgs}
              className="clay-btn w-full text-white py-4 px-6 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <span className="text-sm text-gray-600">Already have an account? </span>
            <Link to="/login" className="text-sm text-blue-500 hover:text-blue-600 font-medium transition-colors">
              Sign in
            </Link>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-400 text-sm mt-8">
          © 2026 Leave Management System. All rights reserved.
        </p>
      </div>
    </div>
  );
}
