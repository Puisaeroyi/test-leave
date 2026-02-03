import http from "./http";

const API_URL = "http://localhost:8000/api/v1/auth";

export async function login({ email, password }) {
  const res = await http.post(`${API_URL}/login/`, {
    email,
    password,
  });

  if (!res.data.user) {
    throw new Error("Invalid email or password");
  }

  // Store tokens in localStorage
  if (res.data.user.tokens) {
    localStorage.setItem("access", res.data.user.tokens.access);
    localStorage.setItem("refresh", res.data.user.tokens.refresh);
  }

  return res.data.user;
}

export async function signup(data) {
  const res = await http.post(`${API_URL}/register/`, {
    email: data.email,
    password: data.password,
    password_confirm: data.password_confirm || data.password,
    first_name: data.firstName || data.first_name || "",
    last_name: data.lastName || data.last_name || "",
    employee_code: data.employeeCode || data.employee_code || null,
    entity: data.entity,
    location: data.location,
    department: data.department,
  });

  // Store tokens in localStorage
  if (res.data.user.tokens) {
    localStorage.setItem("access", res.data.user.tokens.access);
    localStorage.setItem("refresh", res.data.user.tokens.refresh);
  }

  return res.data.user;
}

export async function logout() {
  const refreshToken = localStorage.getItem("refresh");
  if (refreshToken) {
    await http.post(`${API_URL}/logout/`, { refresh: refreshToken });
  }
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
}

export async function getCurrentUser() {
  const res = await http.get(`${API_URL}/me/`);
  return res.data;
}

// Organization APIs for registration dropdowns
const ORG_API_URL = "http://localhost:8000/api/v1/organizations";

export async function getEntities() {
  const res = await http.get(`${ORG_API_URL}/entities/`);
  return res.data;
}

export async function getLocations(entityId) {
  const res = await http.get(`${ORG_API_URL}/locations/?entity_id=${entityId}`);
  return res.data;
}

export async function getDepartments(locationId) {
  const res = await http.get(`${ORG_API_URL}/departments/?location_id=${locationId}`);
  return res.data;
}
