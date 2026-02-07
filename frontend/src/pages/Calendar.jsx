import { useState, useEffect } from "react";
import {
  Calendar,
  Badge,
  Card,
  Typography,
  Select,
  Spin,
  message,
} from "antd";
import dayjs from "dayjs";
import { getTeamCalendar, createLeaveRequest, getLeaveBalance } from "../api/dashboardApi";
import CreateEventModal from "@components/CreateEventModal";
import NewLeaveRequestModal from "@components/NewLeaveRequestModal";
import NewBusinessTripModal from "@components/NewBusinessTripModal";

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

  const [filter, setFilter] = useState("all");
  const [currentDate, setCurrentDate] = useState(dayjs());
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
    // Custom hours leave: show name + time range
    if (!item.is_full_day && item.start_time && item.end_time) {
      return `${item.user} (${item.start_time} - ${item.end_time})`;
    }
    // Business trip: show name + city, country
    if (item.type === "business") {
      return `${item.user} - ${item.city}, ${item.country}`;
    }
    return item.user;
  };

  /* =======================
     RENDER DAY CELL
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

          // Custom hours: render as bullet legend instead of bar
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

          // Full day / holiday / business trip: colored bar
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

  return (
    <>
      <Card
        title="Team Leave Calendar"
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
                { value: "vacation", label: "Vacation only" },
                { value: "holiday", label: "Holidays only" },
              ]}
            />
            {["holiday", "vacation", "sick", "business"].map((type) => (
              <Badge key={type} color={TYPE_STYLE[type].border} text={TYPE_STYLE[type].label} />
            ))}
          </div>
        }
      >
        <Spin spinning={loading}>
          <Calendar
            value={currentDate}
            onPanelChange={(date) => setCurrentDate(date)}
            onSelect={(date, { source }) => {
              if (source === "date" && !date.isBefore(dayjs(), "day")) {
                setSelectedClickDate(date);
                setOpenCreate(true);
              }
            }}
            cellRender={dateCellRender}
          />
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
