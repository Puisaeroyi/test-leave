import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import type { Entity, Location, Department } from '../types';

interface OnboardingPageProps {
  onComplete?: () => void;
}

export default function OnboardingPage({ onComplete }: OnboardingPageProps) {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [entityId, setEntityId] = useState('');
  const [locationId, setLocationId] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const { completeOnboarding, user } = useAuth();
  const navigate = useNavigate();

  // Fetch entities on mount
  useEffect(() => {
    const fetchEntities = async () => {
      try {
        const response = await api.get<{ results: Entity[] }>('/organizations/entities/');
        setEntities(response.data.results || []);
      } catch (error) {
        console.error('Failed to fetch entities:', error);
        // Still show the page even if entities fail to load
        setIsLoadingData(false);
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchEntities();
  }, []);

  // Fetch locations when entity changes
  useEffect(() => {
    if (!entityId) {
      setLocations([]);
      return;
    }

    const fetchLocations = async () => {
      try {
        const response = await api.get<{ results: Location[] }>(`/organizations/locations/?entity=${entityId}`);
        setLocations(response.data.results || []);
      } catch (error) {
        console.error('Failed to fetch locations:', error);
      }
    };

    fetchLocations();
  }, [entityId]);

  // Fetch departments when entity changes
  useEffect(() => {
    if (!entityId) {
      setDepartments([]);
      return;
    }

    const fetchDepartments = async () => {
      try {
        const response = await api.get<{ results: Department[] }>(`/organizations/departments/?entity=${entityId}`);
        setDepartments(response.data.results || []);
      } catch (error) {
        console.error('Failed to fetch departments:', error);
      }
    };

    fetchDepartments();
  }, [entityId]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!entityId) {
      newErrors.entityId = 'Please select an entity';
    }

    if (!locationId) {
      newErrors.locationId = 'Please select a location';
    }

    if (!departmentId) {
      newErrors.departmentId = 'Please select a department';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsLoading(true);

    try {
      await completeOnboarding({
        entity: entityId,
        location: locationId,
        department: departmentId,
      });

      if (onComplete) {
        onComplete();
      } else {
        navigate('/', { replace: true });
      }
    } catch (err: any) {
      console.error('Onboarding error:', err);
      if (err.response?.data) {
        const errorMsg = typeof err.response.data === 'string'
          ? err.response.data
          : err.response.data.error || err.response.data.detail || 'Onboarding failed';
        setErrors({ ...errors, form: errorMsg });
      } else {
        setErrors({ ...errors, form: 'Unable to complete onboarding. Please try again.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleEntityChange = (newEntityId: string) => {
    setEntityId(newEntityId);
    setLocationId('');
    setDepartmentId('');
    if (errors.entityId) setErrors({ ...errors, entityId: '' });
  };

  if (isLoadingData) {
    return (
      <div className="min-h-screen clay-bg flex items-center justify-center px-4">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 text-blue-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-600">Loading organization data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen clay-bg py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="clay-avatar inline-flex items-center justify-center w-16 h-16 mb-5">
            <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Complete Your Profile</h1>
          <p className="text-gray-500">Welcome, {user?.email}! Please fill in your details to get started</p>
        </div>

        {/* Form Card - Claymorphism */}
        <form onSubmit={handleSubmit} className="clay-card p-8">
          <div className="space-y-8">
            {/* Entity Selection Section */}
            <div className="clay-card-inset p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="clay-avatar w-10 h-10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Organization</h3>
                  <p className="text-sm text-gray-500">Select your company entity</p>
                </div>
              </div>
              <select
                id="entity"
                value={entityId}
                onChange={(e) => handleEntityChange(e.target.value)}
                className="clay-select w-full px-5 py-4 text-gray-700 pr-12"
                required
              >
                <option value="">Choose an entity...</option>
                {entities.map((entity) => (
                  <option key={entity.id} value={entity.id}>
                    {entity.name} ({entity.code})
                  </option>
                ))}
              </select>
              {errors.entityId && (
                <p className="mt-2 text-sm text-red-500 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.entityId}
                </p>
              )}
            </div>

            {/* Location Selection Section */}
            <div className="clay-card-inset p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="clay-avatar w-10 h-10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Work Location</h3>
                  <p className="text-sm text-gray-500">Where you'll be working</p>
                </div>
              </div>
              <select
                id="location"
                value={locationId}
                onChange={(e) => {
                  setLocationId(e.target.value);
                  setDepartmentId('');
                  if (errors.locationId) setErrors({ ...errors, locationId: '' });
                }}
                disabled={!entityId}
                className={`clay-select w-full px-5 py-4 text-gray-700 pr-12 ${!entityId ? 'opacity-50 cursor-not-allowed' : ''}`}
                required
              >
                <option value="">
                  {entityId ? 'Choose a location...' : 'Select entity first'}
                </option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name} - {location.city}, {location.country}
                  </option>
                ))}
              </select>
              {errors.locationId && (
                <p className="mt-2 text-sm text-red-500 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.locationId}
                </p>
              )}
            </div>

            {/* Department Selection Section */}
            <div className="clay-card-inset p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="clay-avatar w-10 h-10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Department</h3>
                  <p className="text-sm text-gray-500">Your team assignment</p>
                </div>
              </div>
              <select
                id="department"
                value={departmentId}
                onChange={(e) => {
                  setDepartmentId(e.target.value);
                  if (errors.departmentId) setErrors({ ...errors, departmentId: '' });
                }}
                disabled={!locationId}
                className={`clay-select w-full px-5 py-4 text-gray-700 pr-12 ${!locationId ? 'opacity-50 cursor-not-allowed' : ''}`}
                required
              >
                <option value="">
                  {locationId ? 'Choose a department...' : 'Select location first'}
                </option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name} ({dept.code})
                  </option>
                ))}
              </select>
              {errors.departmentId && (
                <p className="mt-2 text-sm text-red-500 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.departmentId}
                </p>
              )}
            </div>

            {/* Form Error */}
            {errors.form && (
              <div className="clay-card-inset bg-red-50 px-4 py-3 text-red-700 text-sm">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.form}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="clay-btn w-full text-white py-4 px-6 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Completing Setup...
                </span>
              ) : (
                'Complete Setup'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
