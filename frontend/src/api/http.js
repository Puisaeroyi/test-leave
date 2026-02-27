import axios from "axios";

const http = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Generate UUID v4 for idempotency keys
const generateIdempotencyKey = () => {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

// Request interceptor: add Bearer token and idempotency key
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add idempotency key for mutating requests (prevents duplicate submissions)
    if (["post", "put", "patch"].includes(config.method?.toLowerCase())) {
      config.headers["X-Idempotency-Key"] = generateIdempotencyKey();
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 errors with token refresh retry
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem("refresh");
      if (refreshToken) {
        try {
          const res = await axios.post(
            (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api/v1/auth/token/refresh/",
            { refresh: refreshToken }
          );
          const newAccess = res.data.access;
          localStorage.setItem("access", newAccess);
          if (res.data.refresh) {
            localStorage.setItem("refresh", res.data.refresh);
          }
          originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          return http(originalRequest);
        } catch (refreshError) {
          // Refresh failed - clear and redirect
        }
      }

      // Token expired or invalid - clear storage
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Convert relative media paths to full backend URLs
// e.g. "/media/attachments/uuid.pdf" → "https://api.example.com/media/attachments/uuid.pdf"
export const getMediaUrl = (path) => {
  if (!path) return null;
  // Already a full URL — return as-is
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
  return `${base}${path.startsWith("/") ? "" : "/"}${path}`;
};

export default http;
