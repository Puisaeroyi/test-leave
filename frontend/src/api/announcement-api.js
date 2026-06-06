import http from "./http";

const API_URL = "/notifications/announcements";

export const getAnnouncements = async (params = {}) => {
  const response = await http.get(`${API_URL}/`, { params });
  return response.data;
};

export const createAnnouncement = async (data) => {
  const response = await http.post(`${API_URL}/`, data);
  return response.data;
};

export const updateAnnouncement = async (id, data) => {
  const response = await http.patch(`${API_URL}/${id}/`, data);
  return response.data;
};

export const deleteAnnouncement = async (id) => {
  const response = await http.delete(`${API_URL}/${id}/`);
  return response.data;
};
