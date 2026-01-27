import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface NavItem {
  to: string;
  label: string;
  icon: string;
  requiredRoles?: string[];
}

/**
 * Modern Minimal Sidebar Component
 * White background, red active state
 */
export default function Sidebar() {
  const { user, logout } = useAuth();

  const navItems: NavItem[] = [
    { to: '/', label: 'Dashboard', icon: '⌂' },
    { to: '/leaves', label: 'My Leaves', icon: '📅' },
    { to: '/leaves/new', label: 'New Request', icon: '+' },
  ];

  // Manager and above can see approvals
  if (user?.role === 'MANAGER' || user?.role === 'HR' || user?.role === 'ADMIN') {
    navItems.push({ to: '/approvals', label: 'Approvals', icon: '✓' });
  }

  navItems.push({ to: '/calendar', label: 'Team Calendar', icon: '📆' });

  // HR and Admin only
  if (user?.role === 'HR' || user?.role === 'ADMIN') {
    navItems.push({ to: '/admin', label: 'Admin', icon: '⚙' });
  }

  const handleLogout = async () => {
    await logout();
  };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white shadow-md z-10 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <img src="/teampl.ico" alt="TeamPL" className="w-48 h-auto" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-red-50 text-red-600 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`
            }
          >
            <span className="mr-3 text-lg">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section - Settings & Sign Out */}
      <div className="p-4 border-t border-gray-200 space-y-1">
        <NavLink
          to="/settings"
          className="flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <span className="mr-3 text-lg">⚙</span>
          Settings
        </NavLink>
        <button
          onClick={handleLogout}
          className="w-full flex items-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <span className="mr-3 text-lg">→</span>
          Sign out
        </button>
      </div>
    </aside>
  );
}
