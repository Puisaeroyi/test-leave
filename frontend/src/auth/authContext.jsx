import { createContext, useContext, useState } from "react";
import { logout as logoutApi } from "@api/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  const login = (userData) => {
    // Normalize user from backend response
    const normalizedUser = {
      id: userData.id,
      email: userData.email,
      role: userData.role,
      firstName: userData.first_name,
      lastName: userData.last_name,
      name: `${userData.first_name} ${userData.last_name}`,
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
      tokens: userData.tokens,
    };

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
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
