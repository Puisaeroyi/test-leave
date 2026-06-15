import { useState, useEffect, useCallback } from "react";
import {
  Calendar,
  Badge,
  Card,
  Typography,
  Select,
  Spin,
  Grid,
  Space,
  Switch,
  Tag,
  Empty,
  message,
} from "antd";
import dayjs from "dayjs";
import { getTeamCalendar, createLeaveRequest, getLeaveBalance } from "../api/dashboardApi";
import CreateEventModal from "@components/CreateEventModal";
import NewLeaveRequestModal from "@components/NewLeaveRequestModal";
import NewBusinessTripModal from "@components/NewBusinessTripModal";

const { Text } = Typography;
const { useBreakpoint } = Grid;

/* =======================
   STYLE MAP
======================= */
const TYPE_STYLE = {
  holiday: {
    color: "var(--color-danger)",
    bg: "var(--color-danger-soft)",
    border: "var(--color-danger)",
    label: "Holiday",
  },
  vacation: {
    color: "var(--color-accent)",
    bg: "var(--color-accent-soft)",
    border: "var(--color-accent)",
    label: "Vacation",
  },
  sick: {
    color: "var(--color-warning)",
    bg: "var(--color-warning-soft)",
    border: "var(--color-warning)",
    label: "Sick Leave",
  },
  business: {
    color: "var(--color-info)",
    bg: "var(--color-info-soft)",
    border: "var(--color-info)",
    label: "Business Trip",
  },
  remote: {
    color: "var(--color-success)",
    bg: "var(--color-success-soft)",
    border: "var(--color-success)",
    label: "Remote",
  },
};

/* =======================
   MAP CATEGORY TO TYPE
======================= */
const mapCategoryToType = (category) => {
  const cat = (category || "").toLowerCase();
  if (cat.includes("sick")) return "sick";
  if (cat.includes("remote")) return "remote";
  return "vacation";
};

const formatTimeAmPm = (value) => {
  if (!value) return "";
  const [hourPart, minutePart = "00"] = String(value).split(":");
  const hour = Number(hourPart);
  if (Number.isNaN(hour)) return value;
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutePart.padStart(2, "0")} ${period}`;
};

const getScheduleLabel = (item) => {
  if (!item.is_working) return "Off";
  return `${item.shift_name} | ${formatTimeAmPm(item.start_time)} - ${formatTimeAmPm(item.end_time)}`;
};

const getEventKey = (item, index) =>
  [item.id, item.date, item.type, item.user, item.note, item.city, item.country, index]
    .filter(Boolean)
    .join("-");

/* =======================
   TRANSFORM API DATA TO EVENTS
======================= */
function transformToEvents(data) {
  const evts = [];

  // 1. Holidays (multi-day)
  if (data.holidays) {
    data.holidays.forEach((h) => {
      const start = dayjs(h.start_date);
      const end = dayjs(h.end_date);
      for (let d = start; d.isSame(end) || d.isBefore(end); d = d.add(1, "day")) {
        evts.push({
          date: d.format("YYYY-MM-DD"),
          type: "holiday",
          user: "Company",
          note: h.name,
        });
      }
    });
  }

  // 2. Leaves (multi-day)
  if (data.leaves) {
    data.leaves.forEach((leave) => {
      const member = data.team_members?.find((m) => m.id === leave.member_id);
      const start = dayjs(leave.start_date);
      const end = dayjs(leave.end_date);
      for (let d = start; d.isSame(end) || d.isBefore(end); d = d.add(1, "day")) {
        evts.push({
          date: d.format("YYYY-MM-DD"),
          type: mapCategoryToType(leave.category),
          user: member?.name || "Unknown",
          note: leave.category,
          start_time: leave.start_time,
          end_time: leave.end_time,
          is_full_day: leave.is_full_day,
        });
      }
    });
  }

  // 3. Business trips
  if (data.business_trips) {
    data.business_trips.forEach((trip) => {
      const member = data.team_members?.find((m) => m.id === trip.member_id);
      const start = dayjs(trip.start_date);
      const end = dayjs(trip.end_date);
      for (let d = start; d.isSame(end) || d.isBefore(end); d = d.add(1, "day")) {
        evts.push({
          date: d.format("YYYY-MM-DD"),
          type: "business",
          user: member?.name || "Unknown",
          city: trip.city,
          country: trip.country,
          note: `${trip.city}, ${trip.country}`,
        });
      }
    });
  }

  return evts;
}

function transformToWorkSchedule(data) {
  return (data.work_schedule || []).map((item) => ({
    ...item,
    type: "work_schedule",
    note: getScheduleLabel(item),
  }));
}

export default function TeamCalendar() {
  const today = dayjs().format("YYYY-MM-DD");
  const screens = useBreakpoint();
  const isMobile = !screens.lg;

  const [filter, setFilter] = useState("all");
  const [currentDate, setCurrentDate] = useState(dayjs());
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [scheduleEvents, setScheduleEvents] = useState([]);
  const [showWorkSchedule, setShowWorkSchedule] = useState(true);
  const [balance, setBalance] = useState([]);

  // Create event modal states
  const [selectedClickDate, setSelectedClickDate] = useState(null);
  const [openCreate, setOpenCreate] = useState(false);
  const [openLeave, setOpenLeave] = useState(false);
  const [openBusiness, setOpenBusiness] = useState(false);

  /* =======================
     FETCH CALENDAR DATA
  ======================= */
  const fetchCalendarData = useCallback(async () => {
    setLoading(true);
    try {
      const month = currentDate.month() + 1;
      const year = currentDate.year();

      const [data, balanceData] = await Promise.all([
        getTeamCalendar(month, year),
        getLeaveBalance(),
      ]);
      setBalance(balanceData);

      const transformedEvents = transformToEvents(data);
      setEvents(transformedEvents);
      setScheduleEvents(transformToWorkSchedule(data));
    } catch (error) {
      console.error("Failed to load calendar data:", error);
      message.error("Failed to load calendar data");
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  useEffect(() => {
    fetchCalendarData();
  }, [fetchCalendarData]);

  /* =======================
     FILTER BY DATE & TYPE
  ======================= */
  const getEventsByDate = (value) => {
    const date = dayjs(value).format("YYYY-MM-DD");
    return events.filter(
      (e) => e.date === date && (filter === "all" || e.type === filter),
    );
  };

  const getScheduleByDate = (value) => {
    if (!showWorkSchedule) return null;
    const date = dayjs(value).format("YYYY-MM-DD");
    return scheduleEvents.find((item) => item.date === date) || null;
  };

  /* =======================
     BUILD CELL LABEL
  ======================= */
  const getCellLabel = (item) => {
    if (item.type === "holiday") return item.note;
    if (!item.is_full_day && item.start_time && item.end_time) {
      return `${item.user} - ${item.note} (${formatTimeAmPm(item.start_time)} - ${formatTimeAmPm(item.end_time)})`;
    }
    if (item.type === "business") {
      return `${item.user} - ${item.city}, ${item.country}`;
    }
    return item.note ? `${item.user} - ${item.note}` : item.user;
  };

  /* =======================
     HANDLE DATE SELECT
  ======================= */
  const handleDateSelect = (date, info) => {
    setSelectedDate(date);

    // On mobile, also update month when selecting a date from a different month
    if (isMobile && date.month() !== currentDate.month()) {
      setCurrentDate(date);
    }

    // Open create modal for future dates (desktop uses source check, mobile always on tap)
    const source = info?.source;
    if (!date.isBefore(dayjs(), "day")) {
      if (isMobile || source === "date") {
        setSelectedClickDate(date);
        setOpenCreate(true);
      }
    }
  };

  /* =======================
     RENDER DAY CELL (desktop only)
  ======================= */
  const dateCellRender = (value) => {
    const list = getEventsByDate(value);
    const schedule = getScheduleByDate(value);
    const isToday = value.format("YYYY-MM-DD") === today;
    const isPast = value.isBefore(dayjs(), "day");

    return (
      <div
        className="calendar-cell"
        style={{
          cursor: isPast ? "default" : "pointer",
          opacity: isPast ? 0.4 : 1,
          pointerEvents: isPast ? "none" : "auto",
          background: isToday
            ? "linear-gradient(180deg, var(--color-accent-soft), transparent)"
            : "transparent",
        }}
      >
        {isToday && <span className="calendar-today-dot" />}

        {schedule && (
          <div className={`calendar-work-schedule-chip${schedule.is_working ? "" : " calendar-work-schedule-chip--off"}`}>
            <span className="calendar-work-schedule-chip__eyebrow">My shift</span>
            <span className="calendar-work-schedule-chip__label">{getScheduleLabel(schedule)}</span>
          </div>
        )}

        {list.map((item, index) => {
          const style = TYPE_STYLE[item.type];
          const isCustomHours = !item.is_full_day && item.start_time && item.end_time;

          if (isCustomHours) {
            return (
              <Badge
                key={getEventKey(item, index)}
                color={style.border}
                text={
                  <Text style={{ fontSize: 11, color: style.color }}>
                    {getCellLabel(item)}
                  </Text>
                }
                style={{ marginBottom: 2 }}
              />
            );
          }

          return (
            <div
              key={getEventKey(item, index)}
              className="calendar-event-chip"
              style={{
                background: style.bg,
                color: style.border,
              }}
            >
              <Text
                style={{
                  fontSize: 11,
                  color: style.color,
                  fontWeight: 600,
                }}
              >
                {getCellLabel(item)}
              </Text>
            </div>
          );
        })}
      </div>
    );
  };

  const desktopFullCellRender = (value, info) => {
    if (info.type !== "date") return info.originNode;

    const isToday = value.format("YYYY-MM-DD") === today;

    return (
      <div className={`calendar-date-shell${isToday ? " calendar-date-shell--today" : ""}`}>
        <div className="calendar-date-value">{value.date()}</div>
        {dateCellRender(value)}
      </div>
    );
  };

  /* =======================
     MOBILE: event list for selected date
  ======================= */
  const selectedDateEvents = getEventsByDate(selectedDate);
  const selectedDateSchedule = getScheduleByDate(selectedDate);

  /* =======================
     MOBILE: dot indicators on calendar cells
  ======================= */
  const mobileCellRender = (value) => {
    const list = getEventsByDate(value);
    const schedule = getScheduleByDate(value);
    if (list.length === 0 && !schedule) return null;

    // Show colored dots for event types present on this day
    const types = [...new Set([
      ...(schedule ? ["work_schedule"] : []),
      ...list.map((e) => e.type),
    ])];
    return (
      <div className="calendar-mobile-dots">
        {types.slice(0, 3).map((type) => (
          <span
            key={type}
            className="calendar-mobile-dot"
            style={{
              background: type === "work_schedule" ? "var(--color-text-soft)" : TYPE_STYLE[type]?.border || "#999",
            }}
          />
        ))}
      </div>
    );
  };

  /* =======================
     LEGEND BADGES
  ======================= */
  const legendBadges = ["holiday", "vacation", "sick", "business"].map((type) => (
    <Badge key={type} color={TYPE_STYLE[type].border} text={TYPE_STYLE[type].label} />
  ));
  const workScheduleToggle = (
    <Space size={6} className="calendar-work-schedule-toggle">
      <Switch size="small" checked={showWorkSchedule} onChange={setShowWorkSchedule} />
      <span>My Work Shift</span>
    </Space>
  );
  const renderMobileSchedule = () => {
    if (!selectedDateSchedule) return null;
    const className = "calendar-mobile-event calendar-mobile-schedule"
      + (selectedDateSchedule.is_working ? "" : " calendar-mobile-schedule--off");
    return (
      <div className={className}>
        <div className="calendar-mobile-event__bar" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <Text strong style={{ fontSize: 14 }}>
            {getScheduleLabel(selectedDateSchedule)}
          </Text>
          <div>
            <Tag style={{ marginTop: 4, fontSize: 11 }}>My Work Shift</Tag>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="page-shell">
      <section>
        <div className="page-kicker">Team Availability</div>
        <h1 className="page-title">Team Leave Calendar</h1>
        <p className="page-subtitle">
          See holidays, leave plans, and business trips together so the team can plan smoothly.
        </p>
      </section>

      <Card
        className="page-panel"
        title="Team Leave Calendar"
        extra={
          isMobile ? (
            // Mobile: only filter dropdown
            <div className="calendar-filter-row">
              <Select
                value={filter}
                onChange={setFilter}
                style={{ width: 140 }}
                size="small"
                options={[
                  { value: "all", label: "All types" },
                  { value: "business", label: "Business Trip" },
                  { value: "vacation", label: "Vacation" },
                  { value: "holiday", label: "Holidays" },
                ]}
              />
              {workScheduleToggle}
            </div>
          ) : (
            // Desktop: filter + legend badges
            <div className="calendar-filter-row">
              <Select
                value={filter}
                onChange={setFilter}
                style={{ width: 200 }}
                options={[
                  { value: "all", label: "All leave types" },
                  { value: "business", label: "Business Trip only" },
                  { value: "vacation", label: "Vacation only" },
                  { value: "holiday", label: "Holidays only" },
                ]}
              />
              {workScheduleToggle}
              {legendBadges}
            </div>
          )
        }
      >
        <Spin spinning={loading}>
          {isMobile ? (
            /* ===== MOBILE: compact calendar + event list ===== */
            <>
              <Calendar
                fullscreen={false}
                value={selectedDate}
                onPanelChange={(date) => {
                  setCurrentDate(date);
                  setSelectedDate(date);
                }}
                onSelect={(date) => handleDateSelect(date, { source: "date" })}
                fullCellRender={(date, info) => {
                  if (info.type !== "date") return info.originNode;
                  const isSelected = date.isSame(selectedDate, "day");
                  const isToday = date.format("YYYY-MM-DD") === today;
                  const inMonth = date.month() === currentDate.month();

                  return (
                    <div
                      style={{
                        width: "100%",
                        textAlign: "center",
                        padding: "4px 0",
                        opacity: inMonth ? 1 : 0.3,
                      }}
                    >
                      <div
                        style={{
                          width: 28,
                          height: 28,
                          lineHeight: "28px",
                          borderRadius: "50%",
                          margin: "0 auto",
                          background: isSelected ? "var(--color-accent)" : isToday ? "var(--color-accent-soft)" : "transparent",
                          color: isSelected ? "#fff" : undefined,
                          fontWeight: isToday || isSelected ? 600 : 400,
                        }}
                      >
                        {date.date()}
                      </div>
                      {mobileCellRender(date)}
                    </div>
                  );
                }}
              />

              {/* Legend row below compact calendar */}
              <div className="calendar-filter-row" style={{ padding: "12px 0 8px" }}>
                {legendBadges}
              </div>

              {/* Selected date header */}
              <div className="calendar-selected-day">
                <Text strong style={{ fontSize: 15 }}>
                  {selectedDate.format("ddd, MMM D, YYYY")}
                </Text>
                {!selectedDate.isBefore(dayjs(), "day") && (
                  <Typography.Link
                    style={{ float: "right", color: "var(--color-accent)", cursor: "pointer", fontSize: 13 }}
                    onClick={() => {
                      setSelectedClickDate(selectedDate);
                      setOpenCreate(true);
                    }}
                  >
                    + Add event
                  </Typography.Link>
                )}
              </div>

              {/* Event list for selected date */}
              {selectedDateEvents.length === 0 && !selectedDateSchedule ? (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="No events on this day"
                  style={{ padding: "16px 0" }}
                />
              ) : (
                <div className="calendar-event-list">
                  {renderMobileSchedule()}
                  {selectedDateEvents.map((item, index) => {
                    const style = TYPE_STYLE[item.type];
                    return (
                      <div
                        key={getEventKey(item, index)}
                        className="calendar-mobile-event"
                        style={{
                          background: style.bg,
                          color: style.border,
                        }}
                      >
                        <div
                          className="calendar-mobile-event__bar"
                          style={{
                            background: style.border,
                          }}
                        />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <Text strong style={{ color: style.color, fontSize: 14 }}>
                            {getCellLabel(item)}
                          </Text>
                          <div>
                            <Tag
                              color={style.border}
                              style={{ marginTop: 4, fontSize: 11 }}
                            >
                              {TYPE_STYLE[item.type]?.label}
                            </Tag>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            /* ===== DESKTOP: full-size calendar grid ===== */
            <Calendar
              className="team-calendar-grid"
              value={currentDate}
              onPanelChange={(date) => setCurrentDate(date)}
              onSelect={(date, info) => handleDateSelect(date, info)}
              fullCellRender={desktopFullCellRender}
            />
          )}
        </Spin>
      </Card>

      {/* ===== CREATE EVENT TYPE SELECTOR ===== */}
      <CreateEventModal
        open={openCreate}
        onClose={() => setOpenCreate(false)}
        allowLeave={selectedClickDate ? selectedClickDate.diff(dayjs().startOf("day"), "day") >= 3 : true}
        onSelect={(type) => {
          setOpenCreate(false);
          type === "leave" ? setOpenLeave(true) : setOpenBusiness(true);
        }}
      />

      {/* ===== LEAVE REQUEST MODAL ===== */}
      <NewLeaveRequestModal
        open={openLeave}
        onCancel={() => setOpenLeave(false)}
        onSubmit={async (data) => {
          try {
            await createLeaveRequest(data);
            message.success("Leave request submitted");
            fetchCalendarData();
          } catch (error) {
            message.error(error.response?.data?.error || error.message || "Failed to submit request");
          }
        }}
        balances={balance}
        initialDate={selectedClickDate}
      />

      {/* ===== BUSINESS TRIP MODAL ===== */}
      <NewBusinessTripModal
        open={openBusiness}
        onCancel={() => setOpenBusiness(false)}
        onSubmit={() => {
          fetchCalendarData();
        }}
        initialDate={selectedClickDate}
      />
    </div>
  );
}
