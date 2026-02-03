import { useState, useEffect } from "react";
import {
  Calendar,
  Badge,
  Card,
  Typography,
  Drawer,
  Select,
  Tag,
  Divider,
  Empty,
  Spin,
  message,
} from "antd";
import dayjs from "dayjs";
import { getTeamCalendar } from "../api/dashboardApi";

const { Text } = Typography;

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
  pto: {
    color: "#0958d9",
    bg: "rgba(22,119,255,0.12)",
    border: "#1677ff",
    label: "PTO",
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
  return "pto"; // default
};

export default function TeamCalendar() {
  const today = dayjs().format("YYYY-MM-DD");

  const [filter, setFilter] = useState("all");
  const [selectedDate, setSelectedDate] = useState(null);
  const [currentDate, setCurrentDate] = useState(dayjs());
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);

  /* =======================
     FETCH CALENDAR DATA
  ======================= */
  const fetchCalendarData = async () => {
    setLoading(true);
    try {
      const month = currentDate.month() + 1;
      const year = currentDate.year();

      const data = await getTeamCalendar(month, year);
      setCalendarData(data);

      // Transform API data to events
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

    // 1. Add holidays (handle multi-day)
    if (data.holidays) {
      data.holidays.forEach((h) => {
        const start = dayjs(h.start_date);
        const end = dayjs(h.end_date);

        // Generate date range for multi-day holidays
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

    // 2. Add leaves (handle multi-day)
    if (data.leaves) {
      data.leaves.forEach((leave) => {
        const member = data.team_members?.find((m) => m.id === leave.member_id);
        const start = dayjs(leave.start_date);
        const end = dayjs(leave.end_date);

        // Generate date range
        for (let d = start; d.isSame(end) || d.isBefore(end); d = d.add(1, "day")) {
          evts.push({
            date: d.format("YYYY-MM-DD"),
            type: mapCategoryToType(leave.category),
            user: member?.name || "Unknown",
            note: leave.category,
            start_time: leave.start_time,
            end_time: leave.end_time,
          });
        }
      });
    }

    // 3. Add business trips
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
            note: `${trip.city}, ${trip.country} - ${trip.note || ""}`.trim(),
          });
        }
      });
    }

    return evts;
  };

  /* =======================
     FETCH ON DATE CHANGE
  ======================= */
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
     RENDER DAY CELL
  ======================= */
  const dateCellRender = (value) => {
    const list = getEventsByDate(value);
    const isToday = value.format("YYYY-MM-DD") === today;

    return (
      <div
        onClick={() =>
          list.length && setSelectedDate(value.format("YYYY-MM-DD"))
        }
        style={{
          padding: 6,
          borderRadius: 10,
          cursor: list.length ? "pointer" : "default",
          background: isToday
            ? "linear-gradient(180deg, rgba(22,119,255,0.15), transparent)"
            : "transparent",
          position: "relative",
        }}
      >
        {/* TODAY DOT */}
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
                {item.type === 'holiday' ? item.note : item.user}
              </Text>
            </div>
          );
        })}
      </div>
    );
  };

  const selectedEvents = selectedDate
    ? getEventsByDate(dayjs(selectedDate))
    : [];

  return (
    <>
      <Card
        title="📅 Team Leave Calendar"
        style={{ borderRadius: 16 }}
        extra={
          <div style={{ display: "flex", gap: 12 }}>
            <Select
              value={filter}
              onChange={setFilter}
              style={{ width: 200 }}
              options={[
                { value: "all", label: "All leave types" },
                { value: "business", label: "Business Trip only" },
                { value: "pto", label: "PTO only" },
                { value: "holiday", label: "Holidays only" },
              ]}
            />
            {["holiday", "pto", "business"].map((type) => (
              <Badge key={type} color={TYPE_STYLE[type].border} text={TYPE_STYLE[type].label} />
            ))}
          </div>
        }
      >
        <Spin spinning={loading}>
          <Calendar
            value={currentDate}
            onPanelChange={(date) => setCurrentDate(date)}
            cellRender={dateCellRender}
          />
        </Spin>
      </Card>

      {/* =======================
         DRAWER – FULL DAY INFO
      ======================= */}
      <Drawer
        open={!!selectedDate}
        onClose={() => setSelectedDate(null)}
        title={`📅 ${selectedDate}`}
        width={420}
      >
        <Text strong>👥 {selectedEvents.length} people off</Text>

        <Divider />

        {selectedEvents.length === 0 ? (
          <Empty description="No leave on this day" />
        ) : (
          selectedEvents.map((e, i) => {
            const style = TYPE_STYLE[e.type];
            return (
              <Card
                key={i}
                size="small"
                style={{
                  marginBottom: 12,
                  borderLeft: `4px solid ${style.border}`,
                }}
              >
                <Text strong>{e.user}</Text>
                <div style={{ marginTop: 4 }}>
                  <Tag color={style.border}>{style.label}</Tag>
                </div>
                {e.note && (
                  <div style={{ marginTop: 6, fontSize: 12 }}>📝 {e.note}</div>
                )}
                {e.start_time && e.end_time && (
                  <div style={{ marginTop: 4, fontSize: 12 }}>
                    ⏰ {e.start_time} - {e.end_time}
                  </div>
                )}
              </Card>
            );
          })
        )}
      </Drawer>
    </>
  );
}
