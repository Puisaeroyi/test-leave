import { Navigate } from "react-router-dom";
import { useAuth } from "@auth/authContext";

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;

  // Force password change on first login
  if (user.firstLogin) return <Navigate to="/change-password" replace />;

  return children;
}
