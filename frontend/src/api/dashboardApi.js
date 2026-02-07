import http from "./http";

// Note: http.js baseURL already includes /api/v1, so we only add /leaves
const API_URL = "/leaves";

/* ================= FILE UPLOAD ================= */
export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const res = await http.post(`${API_URL}/upload/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data; // { url, filename, size, type }
};

/* ================= LEAVE HISTORY ================= */
export const getLeaveHistory = async (sort = "new") => {
  const res = await http.get(`${API_URL}/requests/my/`);
  const data = res.data;

  // Map backend response to frontend format
  const mapped = data.map((item) => ({
    id: item.id,
    type: item.category?.name || item.leave_category || "Leave",
    from: item.start_date,
    to: item.end_date,
    hours: item.total_hours,
    startTime: item.start_time || null,
    endTime: item.end_time || null,
    status: item.status.charAt(0) + item.status.slice(1).toLowerCase(), // APPROVED -> Approved
    reason: item.reason,
    denyReason: item.rejection_reason,
    attachment: item.attachment_url || null,
  }));

  // Sort by date
  mapped.sort((a, b) =>
    sort === "new"
      ? new Date(b.from) - new Date(a.from)
      : new Date(a.from) - new Date(b.from)
  );

  return mapped;
};

/* ================= CREATE REQUEST ================= */
export const createLeaveRequest = async (formData) => {
  // Get categories to find the category ID based on leaveCategory
  const categories = await getLeaveCategories();

  // Map leaveCategory (vacation/sick) to category name/code
  // Assuming backend has categories with codes like "VACATION", "SICK"
  const categoryMap = {
    vacation: categories.find(c => c.code === "VACATION"),
    sick: categories.find(c => c.code === "SICK"),
  };

  const category = categoryMap[formData.leaveCategory];

  if (!category) {
    throw new Error(`Invalid leave category: ${formData.leaveCategory}`);
  }

  // Map frontend form data to backend format
  const payload = {
    leave_category: category.id,
    exempt_type: formData.exemptType.toUpperCase(), // exempt -> EXEMPT, non-exempt -> NON_EXEMPT
    start_date: formData.date[0].format("YYYY-MM-DD"),
    end_date: formData.date[1].format("YYYY-MM-DD"),
    shift_type: formData.dayType === "custom" ? "CUSTOM_HOURS" : "FULL_DAY",
    start_time: formData.startTime ? formData.startTime.format("HH:mm") : null,
    end_time: formData.endTime ? formData.endTime.format("HH:mm") : null,
    total_hours: formData.totalHours,
    reason: formData.reason,
    attachment_url: formData.attachment_url || null,
  };

  const res = await http.post(`${API_URL}/requests/`, payload);
  return res.data;
};

/* ================= BALANCE ================= */
export const getLeaveBalance = async (year = new Date().getFullYear()) => {
  const res = await http.get(`${API_URL}/balances/me/`, {
    params: { year },
  });
  const data = res.data;

  // Map backend 4-balance response to frontend format
  // Backend returns: { balances: [{ type, label, allocated_hours, used_hours, remaining_hours }, ...] }
  return data.balances || [];
};

/* ================= TEAM CALENDAR DATA ================= */
export const getTeamCalendar = async (month, year, memberIds = []) => {
  const res = await http.get(`${API_URL}/calendar/`, {
    params: { month, year, member_ids: memberIds },
  });
  return res.data;
};

/* ================= UPCOMING EVENTS (for Dashboard widget) ================= */
export const getUpcomingEvents = async () => {
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();

  const data = await getTeamCalendar(month, year);

  const events = [];

  // Add holidays
  if (data.holidays) {
    data.holidays.forEach((h) => {
      events.push({
        id: `holiday-${h.start_date}`,
        title: h.name,
        from: h.start_date,
        to: h.end_date,
        type: "holiday",
      });
    });
  }

  // Add approved leaves (my team)
  if (data.leaves) {
    const userId = localStorage.getItem("user_id");
    data.leaves.forEach((l) => {
      const displayName = l.member_id === userId ? "You" : l.member_name;
      events.push({
        id: l.id,
        title: displayName,
        from: l.start_date,
        to: l.end_date,
        type: "Vacation",
      });
    });
  }

  // Add business trips
  if (data.business_trips) {
    const userId = localStorage.getItem("user_id");
    data.business_trips.forEach((b) => {
      const displayName = b.member_id === userId ? "You" : b.member_name;
      events.push({
        id: `trip-${b.id}`,
        title: `${displayName} - ${b.city}, ${b.country}`,
        from: b.start_date,
        to: b.end_date,
        type: "business",
      });
    });
  }

  // Sort by date
  events.sort((a, b) => new Date(a.from) - new Date(b.from));

  return events.slice(0, 10); // Limit to 10 events
};

/* ================= GET LEAVE CATEGORIES (for dropdown) ================= */
export const getLeaveCategories = async () => {
  const res = await http.get(`${API_URL}/categories/`);
  return res.data.map((cat) => ({
    id: cat.id,
    name: cat.name,
    code: cat.code,
    requiresDocument: cat.requires_document,
  }));
};

/* ================= MANAGER: PENDING REQUESTS (includes Approved for denial) ================= */
export const getPendingRequests = async () => {
  const res = await http.get(`${API_URL}/requests/`, {
    params: { my: "false", status: "pending" },
  });

  // Backend returns paginated response: { count, next, previous, results }
  const data = res.data.results || [];

  // Map backend response to frontend format (hide Cancelled only)
  const statusLabel = { PENDING: "Pending", APPROVED: "Approved", REJECTED: "Denied" };
  return data
    .filter(item => ['PENDING', 'APPROVED', 'REJECTED'].includes(item.status))
    .map((item) => ({
      id: item.id,
    employee: item.user_email || item.user?.email || "Unknown",
    employeeName: item.user_name || `${item.user?.first_name || ""} ${item.user?.last_name || ""}`.trim() || "Unknown",
    type: item.category?.name || "Leave",
    exemptType: item.exempt_type === "NON_EXEMPT" ? "Non-Exempt" : "Exempt",
    from: item.start_date,
    to: item.end_date,
    hours: item.total_hours,
    startTime: item.start_time || null,
    endTime: item.end_time || null,
    status: statusLabel[item.status] || item.status,
    reason: item.reason,
    attachment: item.attachment_url || null,
    denyReason: item.rejection_reason,
    approverComment: item.approver_comment || null,
  }))
    .sort((a, b) => {
      // Sort: Pending first, then by date
      if (a.status === "Pending" && b.status !== "Pending") return -1;
      if (a.status !== "Pending" && b.status === "Pending") return 1;
      return new Date(a.from) - new Date(b.from);
    });
};

/* ================= MANAGER: APPROVE REQUEST ================= */
export const approveLeaveRequest = async (id, comment = "") => {
  const res = await http.post(`${API_URL}/requests/${id}/approve/`, {
    comment,
  });
  return res.data;
};

/* ================= EXPORT APPROVED LEAVES ================= */
export const exportApprovedLeaves = async (startDate, endDate) => {
  const res = await http.get(`${API_URL}/export/approved/`, {
    params: { start_date: startDate, end_date: endDate },
    responseType: "blob",
  });
  return res.data;
};

/* ================= MANAGER: REJECT REQUEST ================= */
export const rejectLeaveRequest = async (id, reason) => {
  const res = await http.post(`${API_URL}/requests/${id}/reject/`, {
    reason,
  });
  return res.data;
};
