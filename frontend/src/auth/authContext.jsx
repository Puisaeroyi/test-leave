import { createContext, useContext, useState } from "react";
import { logout as logoutApi } from "@api/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  const normalizeUser = (userData) => ({
    id: userData.id,
    email: userData.email,
    role: userData.role,
    firstName: userData.first_name,
    lastName: userData.last_name,
    name: `${userData.first_name} ${userData.last_name}`,
    firstLogin: userData.first_login,
    avatar: userData.avatar_url || null,
    entity: {
      id: userData.entity_id,
      name: userData.entity_name,
    },
    location: {
      id: userData.location_id,
      name: userData.location_name,
    },
    department: {
      id: userData.department_id,
      name: userData.department_name,
    },
    isApprover: userData.is_approver || false,
    tokens: userData.tokens,
  });

  const login = (userData) => {
    const normalizedUser = normalizeUser(userData);
    setUser(normalizedUser);
    localStorage.setItem("user", JSON.stringify(normalizedUser));
  };

  const updateUser = (userData) => {
    const normalizedUser = normalizeUser(userData);
    setUser(normalizedUser);
    localStorage.setItem("user", JSON.stringify(normalizedUser));
  };

  const logout = async () => {
    // Call backend API to blacklist refresh token
    try {
      await logoutApi();
    } catch (err) {
      console.error("Logout error:", err);
    }
    // Clear local state
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider value={{ user, login, updateUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
