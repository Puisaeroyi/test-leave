import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute, HRProtectedRoute } from './components/common';
import { Layout } from './components/layout';

// Auth pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import OnboardingPage from './pages/OnboardingPage';

// Dashboard
import DashboardPage from './pages/DashboardPage';

// Leave Request
import LeaveRequestPage from './pages/LeaveRequestPage';
import LeaveListPage from './pages/LeaveListPage';

// Calendar
import CalendarPage from './pages/CalendarPage';

// Approvals
import ApprovalsPage from './pages/ApprovalsPage';

// Admin pages
import AdminDashboard from './pages/admin/AdminDashboard';
import ReportsPage from './pages/admin/ReportsPage';

function AdminPage() {
  return (
    <Layout title="Admin Panel">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-xl font-semibold mb-4">Administration</h2>
        <p className="text-gray-600">Admin panel coming soon...</p>
      </div>
    </Layout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <OnboardingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leaves"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <LeaveListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leaves/new"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <LeaveRequestPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/calendar"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <CalendarPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/approvals"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <ApprovalsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <AdminPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <HRProtectedRoute>
                  <Layout title="User Management">
                    <AdminDashboard />
                  </Layout>
                </HRProtectedRoute>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/reports"
            element={
              <ProtectedRoute requireOnboarding={true}>
                <HRProtectedRoute>
                  <Layout title="Reports">
                    <ReportsPage />
                  </Layout>
                </HRProtectedRoute>
              </ProtectedRoute>
            }
          />

          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
