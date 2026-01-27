import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface HRProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * HR/Admin Protected Route Component
 * Only allows access to users with HR or ADMIN role
 */
export default function HRProtectedRoute({ children }: HRProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'HR' && user?.role !== 'ADMIN') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
