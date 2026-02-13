import http from "./http";

const API_URL = "/notifications";

/* ================= GET NOTIFICATIONS ================= */
export const getNotifications = async (params = {}) => {
  const res = await http.get(API_URL, { params });
  return res.data;
};

/* ================= GET UNREAD COUNT ================= */
export const getUnreadCount = async () => {
  const res = await http.get(`${API_URL}/unread-count/`);
  return res.data.count;
};

/* ================= MARK AS READ ================= */
export const markAsRead = async (id) => {
  const res = await http.patch(`${API_URL}/${id}/`);
  return res.data;
};

/* ================= MARK ALL AS READ ================= */
export const markAllAsRead = async () => {
  const res = await http.post(`${API_URL}/mark-all-read/`);
  return res.data;
};

/* ================= DELETE NOTIFICATION ================= */
export const deleteNotification = async (id) => {
  const res = await http.delete(`${API_URL}/${id}/`);
  return res.data;
};

/* ================= DISMISS ALL NOTIFICATIONS ================= */
export const dismissAllNotifications = async () => {
  const res = await http.delete(`${API_URL}/dismiss-all/`);
  return res.data;
};
