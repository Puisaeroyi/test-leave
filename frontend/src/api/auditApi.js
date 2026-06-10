import http from "./http";

export const getAuditLogs = async (params = {}) => {
  const response = await http.get("/notifications/audit-logs/", { params });
  return response.data;
};
