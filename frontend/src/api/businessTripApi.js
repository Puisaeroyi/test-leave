import http from "./http";

const API_URL = "http://localhost:8000/api/v1/leaves/business-trips";

/**
 * Get user's business trips (paginated)
 * @param {Object} params - Query params { page, page_size }
 * @returns {Promise<{count: number, results: []}>}
 */
export async function getBusinessTrips(params = {}) {
  const { page = 1, page_size = 20 } = params;
  const res = await http.get(`${API_URL}/`, {
    params: { page, page_size },
  });
  return res.data;
}

/**
 * Get single business trip detail
 * @param {string} id - Trip UUID
 * @returns {Promise<Object>}
 */
export async function getBusinessTripDetail(id) {
  const res = await http.get(`${API_URL}/${id}/`);
  return res.data;
}

/**
 * Create new business trip
 * @param {Object} data - Trip data
 * @param {string} data.city - City name
 * @param {string} data.country - Country name
 * @param {Array} data.date - [dayjs, dayjs] date range
 * @param {string} data.note - Optional note
 * @param {string} data.attachment_url - Optional attachment URL
 * @returns {Promise<Object>}
 */
export async function createBusinessTrip(data) {
  const payload = {
    city: data.city,
    country: data.country,
    start_date: data.date[0].format("YYYY-MM-DD"),
    end_date: data.date[1].format("YYYY-MM-DD"),
    note: data.note || "",
    attachment_url: data.attachment_url || "",
  };

  const res = await http.post(`${API_URL}/`, payload);
  return res.data;
}

/**
 * Cancel/delete a business trip
 * @param {string} id - Trip UUID
 * @returns {Promise<{message: string}>}
 */
export async function cancelBusinessTrip(id) {
  const res = await http.post(`${API_URL}/${id}/cancel/`);
  return res.data;
}
