import http from "./http";

export const getHolidayCalendars = async (params = {}) => {
  const response = await http.get("/leaves/holiday-calendars/", { params });
  return response.data.results || [];
};

export const getHolidayCalendar = async (id) => {
  const response = await http.get(`/leaves/holiday-calendars/${id}/`);
  return response.data;
};

export const previewHolidayCalendarGeneration = async (year, countryOverrides = {}) => {
  const response = await http.post("/leaves/holiday-calendars/generation-preview/", {
    year,
    country_overrides: countryOverrides,
  });
  return response.data.results || [];
};

export const generateHolidayCalendars = async (year, countryOverrides = {}) => {
  const response = await http.post("/leaves/holiday-calendars/generate/", {
    year,
    country_overrides: countryOverrides,
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

export const previewPublishHolidayCalendar = async (id) => {
  const response = await http.post(`/leaves/holiday-calendars/${id}/publish-preview/`);
  return response.data;
};

export const previewUnpublishHolidayCalendar = async (id) => {
  const response = await http.post(`/leaves/holiday-calendars/${id}/unpublish-preview/`);
  return response.data;
};

export const unpublishHolidayCalendar = async (id, previewToken) => {
  const response = await http.post(`/leaves/holiday-calendars/${id}/unpublish/`, {
    preview_token: previewToken,
  });
  return response.data;
};

export const getApplicableHolidays = async (year) => {
  const response = await http.get("/leaves/holidays/", { params: { year } });
  return response.data;
};
