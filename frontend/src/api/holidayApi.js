import http from "./http";

export const getHolidayCalendars = async (params = {}) => {
  const response = await http.get("/leaves/holiday-calendars/", { params });
  return response.data.results || [];
};

export const getHolidayCalendar = async (id) => {
  const response = await http.get(`/leaves/holiday-calendars/${id}/`);
  return response.data;
};

export const deleteHolidayCalendar = async (id) => http.delete(`/leaves/holiday-calendars/${id}/`);

export const generateHolidayCalendars = async (year) => {
  const response = await http.post("/leaves/holiday-calendars/generate/", {
    year,
  });
  return response.data.results || [];
};

export const addHoliday = async (calendarId, data) => {
  const response = await http.post(`/leaves/holiday-calendars/${calendarId}/holidays/`, data);
  return response.data;
};

export const updateHoliday = async (id, data) => {
  const response = await http.patch(`/leaves/holidays/${id}/`, data);
  return response.data;
};

export const deleteHoliday = async (id) => http.delete(`/leaves/holidays/${id}/`);

export const publishHolidayCalendar = async (id) => {
  const response = await http.post(`/leaves/holiday-calendars/${id}/publish/`);
  return response.data;
};

export const unpublishHolidayCalendar = async (id) => {
  const response = await http.post(`/leaves/holiday-calendars/${id}/unpublish/`);
  return response.data;
};
