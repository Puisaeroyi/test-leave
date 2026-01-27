import { useAuth } from '../../contexts/AuthContext';
import NotificationCenter from '../notifications/NotificationCenter';

/**
 * Modern Minimal Header Component
 * White background, notifications
 */
export default function Header({ title }: { title?: string }) {
  const { user } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Page Title */}
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{title || 'Dashboard'}</h1>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
          {/* Notification Center */}
          <NotificationCenter />

          {/* User Info */}
          <div className="flex items-center gap-3">
            {/* Avatar */}
            <div className="w-9 h-9 rounded-full bg-red-100 flex items-center justify-center">
              <span className="text-sm font-medium text-red-600">
                {user?.email?.[0].toUpperCase() || 'U'}
              </span>
            </div>
            {/* User Details */}
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">
                {`${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'User'}
              </div>
              <div className="text-xs text-gray-500">
                {user?.role} {user?.entity_name ? `• ${user.entity_name}` : ''}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
