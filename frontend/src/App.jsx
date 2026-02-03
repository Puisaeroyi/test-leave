import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@auth/authContext";
import ProtectedRoute from "@router/protectedRoute";
import MainLayout from "@layouts/mainLayout";

import Login from "@pages/login";
import Signup from "@pages/signup";
import Profile from "@pages/Profile";
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
          <Route path="/signup" element={<Signup />} />

          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/profile" element={<Profile />} />
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
