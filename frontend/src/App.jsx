import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@auth/authContext";
import ProtectedRoute from "@router/protectedRoute";
import MainLayout from "@layouts/mainLayout";

import Login from "@pages/login";
import ChangePassword from "@pages/change-password";
import Profile from "@pages/Profile";
import Settings from "@pages/Settings";
import Dashboard from "@pages/dashBoard";
import TeamCalendar from "@pages/Calendar";
import ManagerTickets from "@pages/ManagerTicket";
import BusinessTripHistory from "@pages/BusinessTripHistory";


export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/change-password" element={<ChangePassword />} />

          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/calendar" element={<TeamCalendar />} />
            <Route path="/manager" element={<ManagerTickets />} />
            <Route path="/business-trip" element={<BusinessTripHistory />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
