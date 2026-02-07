import http from "./http";

/**
 * Get all users (HR/Admin only)
 * Supports filters: ?role=EMPLOYEE&status=ACTIVE&entity=xxx&location=xxx&department=xxx
 */
export const getAllUsers = async (params = {}) => {
  const response = await http.get("/auth/users/", { params });
  return response.data;
};

/**
 * Get user by ID
 */
export const getUserById = async (id) => {
  const response = await http.get(`/auth/users/${id}/`);
  return response.data;
};

/**
 * Update user (HR/Admin can set approver)
 * data: { first_name, last_name, email, employee_code, approver }
 */
export const updateUser = async (id, data) => {
  const response = await http.patch(`/auth/users/${id}/`, data);
  return response.data;
};

/**
 * Delete user (Admin only)
 */
export const deleteUser = async (id) => {
  const response = await http.delete(`/auth/users/${id}/`);
  return response.data;
};

/**
 * Create new user (HR/Admin only)
 * Password auto-set to DEFAULT_IMPORT_PASSWORD with first_login=True
 */
export const createUser = async (data) => {
  const response = await http.post("/auth/users/", data);
  return response.data;
};

/**
 * Get subordinates for current user (users who have current user as approver)
 */
export const getMySubordinates = async () => {
  const response = await http.get("/auth/users/my-subordinates/");
  return response.data;
};
