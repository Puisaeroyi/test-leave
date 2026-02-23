import { useState, useEffect } from "react";
import {
  Calendar,
  Badge,
  Card,
  Typography,
  Select,
  Spin,
  Grid,
  Space,
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
    color: "#cf1322",
    bg: "rgba(255,77,79,0.15)",
    border: "#ff4d4f",
    label: "Holiday",
  },
  vacation: {
    color: "#0958d9",
    bg: "rgba(22,119,255,0.12)",
    border: "#1677ff",
    label: "Vacation",
  },
  sick: {
    color: "#ad4e00",
    bg: "rgba(250,140,22,0.15)",
    border: "#fa8c16",
    label: "Sick Leave",
  },
  business: {
    color: "#531dab",
    bg: "rgba(114,46,209,0.15)",
    border: "#722ed1",
    label: "Business Trip",
  },
  remote: {
    color: "#237804",
    bg: "rgba(82,196,26,0.15)",
    border: "#52c41a",
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

export default function TeamCalendar() {
  const today = dayjs().format("YYYY-MM-DD");
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const [filter, setFilter] = useState("all");
  const [currentDate, setCurrentDate] = useState(dayjs());
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [balance, setBalance] = useState([]);

  // Create event modal states
  const [selectedClickDate, setSelectedClickDate] = useState(null);
  const [openCreate, setOpenCreate] = useState(false);
  const [openLeave, setOpenLeave] = useState(false);
  const [openBusiness, setOpenBusiness] = useState(false);

  /* =======================
     FETCH CALENDAR DATA
  ======================= */
  const fetchCalendarData = async () => {
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
    } catch (error) {
      console.error("Failed to load calendar data:", error);
      message.error("Failed to load calendar data");
    } finally {
      setLoading(false);
    }
  };

  /* =======================
     TRANSFORM API DATA TO EVENTS
  ======================= */
  const transformToEvents = (data) => {
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
  };

  useEffect(() => {
    fetchCalendarData();
  }, [currentDate]);

  /* =======================
     FILTER BY DATE & TYPE
  ======================= */
  const getEventsByDate = (value) => {
    const date = dayjs(value).format("YYYY-MM-DD");
    return events.filter(
      (e) => e.date === date && (filter === "all" || e.type === filter),
    );
  };

  /* =======================
     BUILD CELL LABEL
  ======================= */
  const getCellLabel = (item) => {
    if (item.type === "holiday") return item.note;
    if (!item.is_full_day && item.start_time && item.end_time) {
      return `${item.user} (${item.start_time} - ${item.end_time})`;
    }
    if (item.type === "business") {
      return `${item.user} - ${item.city}, ${item.country}`;
    }
    return item.user;
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
    const isToday = value.format("YYYY-MM-DD") === today;
    const isPast = value.isBefore(dayjs(), "day");

    return (
      <div
        style={{
          padding: 6,
          borderRadius: 10,
          cursor: isPast ? "default" : "pointer",
          opacity: isPast ? 0.4 : 1,
          pointerEvents: isPast ? "none" : "auto",
          background: isToday
            ? "linear-gradient(180deg, rgba(22,119,255,0.15), transparent)"
            : "transparent",
          position: "relative",
        }}
      >
        {isToday && (
          <span
            style={{
              position: "absolute",
              top: 4,
              right: 6,
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "#1677ff",
            }}
          />
        )}

        {list.map((item, index) => {
          const style = TYPE_STYLE[item.type];
          const isCustomHours = !item.is_full_day && item.start_time && item.end_time;

          if (isCustomHours) {
            return (
              <Badge
                key={index}
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
              key={index}
              style={{
                marginBottom: 4,
                padding: "2px 6px",
                borderRadius: 6,
                background: style.bg,
                border: `1px solid ${style.border}`,
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

  /* =======================
     MOBILE: event list for selected date
  ======================= */
  const selectedDateEvents = getEventsByDate(selectedDate);

  /* =======================
     MOBILE: dot indicators on calendar cells
  ======================= */
  const mobileCellRender = (value) => {
    const list = getEventsByDate(value);
    if (list.length === 0) return null;

    // Show colored dots for event types present on this day
    const types = [...new Set(list.map((e) => e.type))];
    return (
      <div style={{ display: "flex", justifyContent: "center", gap: 2, marginTop: 2 }}>
        {types.slice(0, 3).map((type) => (
          <span
            key={type}
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: TYPE_STYLE[type]?.border || "#999",
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

  return (
    <>
      <Card
        title="Team Leave Calendar"
        style={{ borderRadius: 16 }}
        extra={
          isMobile ? (
            // Mobile: only filter dropdown
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
          ) : (
            // Desktop: filter + legend badges
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
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
                          background: isSelected ? "#1677ff" : isToday ? "rgba(22,119,255,0.15)" : "transparent",
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
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", padding: "12px 0 8px" }}>
                {legendBadges}
              </div>

              {/* Selected date header */}
              <div style={{ padding: "8px 0 12px", borderTop: "1px solid #f0f0f0" }}>
                <Text strong style={{ fontSize: 15 }}>
                  {selectedDate.format("ddd, MMM D, YYYY")}
                </Text>
                {!selectedDate.isBefore(dayjs(), "day") && (
                  <Text
                    type="link"
                    style={{ float: "right", color: "#1677ff", cursor: "pointer", fontSize: 13 }}
                    onClick={() => {
                      setSelectedClickDate(selectedDate);
                      setOpenCreate(true);
                    }}
                  >
                    + Add event
                  </Text>
                )}
              </div>

              {/* Event list for selected date */}
              {selectedDateEvents.length === 0 ? (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="No events on this day"
                  style={{ padding: "16px 0" }}
                />
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {selectedDateEvents.map((item, index) => {
                    const style = TYPE_STYLE[item.type];
                    return (
                      <div
                        key={index}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          padding: 12,
                          borderRadius: 10,
                          background: style.bg,
                          border: `1px solid ${style.border}`,
                        }}
                      >
                        <div
                          style={{
                            width: 4,
                            height: 36,
                            borderRadius: 2,
                            background: style.border,
                            flexShrink: 0,
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
              value={currentDate}
              onPanelChange={(date) => setCurrentDate(date)}
              onSelect={(date, info) => handleDateSelect(date, info)}
              cellRender={dateCellRender}
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
    </>
  );
}
