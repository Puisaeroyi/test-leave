import { createContext, useContext, useState } from "react";
import { logout as logoutApi } from "@api/authApi";

const AuthContext = createContext(null);

const textValue = (...values) => {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value;
  }
  return null;
};

const objectId = (...values) => {
  for (const value of values) {
    if (value !== undefined && value !== null && typeof value !== "object") {
      return value;
    }
  }
  return null;
};

const normalizeNamedReference = (flatId, flatName, nested, nameKeys = ["name"]) => {
  if (!nested || typeof nested !== "object") {
    return {
      id: flatId ?? null,
      name: textValue(flatName, typeof nested === "string" ? nested : null),
    };
  }

  return {
    id: objectId(flatId, nested.id),
    name: textValue(flatName, ...nameKeys.map((key) => nested[key])),
  };
};

const normalizeUser = (userData) => {
  const firstName = userData.first_name ?? userData.firstName ?? "";
  const lastName = userData.last_name ?? userData.lastName ?? "";
  const name = textValue(
    userData.name,
    `${firstName} ${lastName}`.trim(),
    userData.email
  );

  return {
    id: userData.id,
    email: userData.email,
    role: userData.role,
    firstName,
    lastName,
    name,
    firstLogin: userData.first_login ?? userData.firstLogin,
    avatar: userData.avatar_url || userData.avatar || null,
    entity: normalizeNamedReference(
      userData.entity_id,
      userData.entity_name,
      userData.entity,
      ["entity_name", "name"]
    ),
    location: normalizeNamedReference(
      userData.location_id,
      userData.location_name,
      userData.location,
      ["location_name", "name"]
    ),
    department: normalizeNamedReference(
      userData.department_id,
      userData.department_name,
      userData.department,
      ["department_name", "name"]
    ),
    isApprover: userData.is_approver ?? userData.isApprover ?? false,
    tokens: userData.tokens,
  };
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    if (!stored) return null;

    try {
      const normalizedUser = normalizeUser(JSON.parse(stored));
      localStorage.setItem("user", JSON.stringify(normalizedUser));
      return normalizedUser;
    } catch {
      localStorage.removeItem("user");
      return null;
    }
  });

  const login = (userData) => {
    const normalizedUser = normalizeUser(userData);
    sessionStorage.removeItem(`announcements:auto-opened:${normalizedUser.id}`);
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
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
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
