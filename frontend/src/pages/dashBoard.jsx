import {
  Row,
  Col,
  Card,
  Table,
  Tag,
  Button,
  Select,
  message,
  Modal,
  Descriptions,
  Typography,
  Space,
} from "antd";
import { PaperClipOutlined, LeftOutlined, RightOutlined } from "@ant-design/icons";
import { useState, useEffect, useMemo, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import dayjs from "dayjs";
import isoWeek from "dayjs/plugin/isoWeek";
import isSameOrAfter from "dayjs/plugin/isSameOrAfter";
import isSameOrBefore from "dayjs/plugin/isSameOrBefore";
import NewLeaveRequestModal from "@components/NewLeaveRequestModal";
import { BalanceMeter, EventCard, MetricCard, StatusPill } from "@components/dashboard/dashboard-widgets";
import {
  getLeaveHistory,
  getLeaveBalance,
  getUpcomingEvents,
  createLeaveRequest,
  updateLeaveRequest,
} from "../api/dashboardApi";
import { getMediaUrl } from "../api/http";
import ApprovalProgress from "../components/ApprovalProgress";
import ResponsiveRecordCard, { ResponsiveRecordRow } from "../components/ResponsiveRecordCard";

dayjs.extend(isoWeek);
dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);

// Build a dayjs for the Monday of a given ISO week/year
const weekOf = (week, year) => dayjs(`${year}-01-04`).isoWeek(week);

const { Text } = Typography;

const EVENT_STYLE = {
  holiday: {
    bg: "var(--color-warning-soft)",
    badge: "var(--color-warning)",
    tagStyle: { color: "var(--color-warning)", background: "var(--color-warning-soft)", border: "1px solid var(--color-warning)" },
    label: "Holiday",
  },
  Vacation: {
    bg: "var(--color-accent-soft)",
    badge: "var(--color-accent)",
    tagStyle: { color: "var(--color-accent)", background: "var(--color-accent-soft)", border: "1px solid var(--color-accent)" },
    label: "Vacation",
  },
  business: {
    bg: "var(--color-info-soft)",
    badge: "var(--color-info)",
    tagStyle: { color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" },
    label: "Business Trip",
  },
};

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();

  const [history, setHistory] = useState([]);
  const [balance, setBalance] = useState([]); // Array of 4 balances
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [sort, setSort] = useState("new");
  const [openModal, setOpenModal] = useState(false);
  const [editRecord, setEditRecord] = useState(null);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [openDetail, setOpenDetail] = useState(false);
  const [loading, setLoading] = useState(true);

  // Week navigation state
  const [currentWeek, setCurrentWeek] = useState(dayjs().isoWeek());
  const [currentYear, setCurrentYear] = useState(dayjs().isoWeekYear());
  const eventCacheRef = useRef({});

  const dashboardMetrics = useMemo(() => {
    const pendingCount = history.filter((item) => item.status === "Pending").length;
    const approvedCount = history.filter((item) => item.status === "Approved").length;
    const deniedCount = history.filter((item) => ["Denied", "Rejected"].includes(item.status)).length;

    return [
      {
        label: "Pending",
        value: pendingCount,
        meta: "Requests waiting for review",
      },
      {
        label: "Approved",
        value: approvedCount,
        meta: "Requests approved in history",
      },
      {
        label: "Deny",
        value: deniedCount,
        meta: "Requests denied in history",
      },
      {
        label: "This Week",
        value: upcomingEvents.length,
        meta: `Week ${currentWeek} team events`,
      },
    ];
  }, [history, upcomingEvents.length, currentWeek]);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [historyData, balanceData] = await Promise.all([
          getLeaveHistory(sort),
          getLeaveBalance(),
        ]);
        setHistory(historyData);
        setBalance(balanceData);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        message.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [sort]);

  // Fetch events for selected week
  useEffect(() => {
    const fetchEventsForWeek = async () => {
      try {
        const weekStart = weekOf(currentWeek, currentYear).startOf("isoWeek");
        const weekEnd = weekOf(currentWeek, currentYear).endOf("isoWeek");

        const startMonth = weekStart.month() + 1;
        const startYear = weekStart.year();
        const endMonth = weekEnd.month() + 1;
        const endYear = weekEnd.year();

        // Fetch both months if week spans month boundary
        const monthsToFetch = [];
        const cacheKey1 = `${startYear}-${String(startMonth).padStart(2, "0")}`;
        const cachedEvents = eventCacheRef.current;
        if (!cachedEvents[cacheKey1]) {
          monthsToFetch.push({ month: startMonth, year: startYear, key: cacheKey1 });
        }

        if (startMonth !== endMonth || startYear !== endYear) {
          const cacheKey2 = `${endYear}-${String(endMonth).padStart(2, "0")}`;
          if (!cachedEvents[cacheKey2]) {
            monthsToFetch.push({ month: endMonth, year: endYear, key: cacheKey2 });
          }
        }

        let nextCache = cachedEvents;

        // Fetch uncached months
        if (monthsToFetch.length > 0) {
          const results = await Promise.all(
            monthsToFetch.map(({ month, year }) => getUpcomingEvents(month, year))
          );

          nextCache = { ...cachedEvents };
          monthsToFetch.forEach(({ key }, idx) => {
            nextCache[key] = results[idx];
          });
          eventCacheRef.current = nextCache;
        }

        // Combine events from both months
        const allEvents = [
          ...(nextCache[cacheKey1] || []),
          ...(startMonth !== endMonth || startYear !== endYear ? nextCache[`${endYear}-${String(endMonth).padStart(2, "0")}`] || [] : []),
        ];

        // Filter events within selected week
        const weekEvents = allEvents.filter((e) => {
          const eventStart = dayjs(e.from);
          const eventEnd = dayjs(e.to);
          return (
            (eventStart.isSameOrAfter(weekStart, "day") && eventStart.isSameOrBefore(weekEnd, "day")) ||
            (eventEnd.isSameOrAfter(weekStart, "day") && eventEnd.isSameOrBefore(weekEnd, "day")) ||
            (eventStart.isBefore(weekStart, "day") && eventEnd.isAfter(weekEnd, "day"))
          );
        });

        setUpcomingEvents(weekEvents);
      } catch (error) {
        console.error("Failed to fetch events for week:", error);
        message.error("Failed to load events");
      }
    };

    fetchEventsForWeek();
  }, [currentWeek, currentYear]);

  // Auto-open request detail modal from notification click
  useEffect(() => {
    const openRequestId = location.state?.openRequestId;
    if (!openRequestId) return;

    // Clear state immediately to prevent re-opening on refresh
    navigate(location.pathname, { replace: true, state: null });

    // Always fetch fresh data then find the request
    const fetchAndOpen = async () => {
      try {
        const data = await getLeaveHistory(sort);
        setHistory(data);
        const found = data.find(r => String(r.id) === String(openRequestId));
        if (found) {
          setSelectedRequest(found);
          setOpenDetail(true);
        }
      } catch (err) {
        console.error("Failed to fetch request for notification:", err);
      }
    };
    fetchAndOpen();
  }, [location.pathname, location.state, navigate, sort]);

  const refreshHistory = async () => {
    const [historyData, balanceData] = await Promise.all([
      getLeaveHistory(sort),
      getLeaveBalance(),
    ]);
    setHistory(historyData);
    setBalance(balanceData);
    eventCacheRef.current = {};
    return historyData;
  };

  const handleCreateRequest = async (data) => {
    if (editRecord) {
      const updated = await updateLeaveRequest(
        editRecord.id,
        data,
        data.expectedUpdatedAt || editRecord.updatedAt,
      );
      message.success("Request updated");
      const historyData = await refreshHistory();
      const refreshed = historyData.find((h) => h.id === editRecord.id);
      if (refreshed) setSelectedRequest(refreshed);
      else if (updated) {
        setSelectedRequest((prev) => (prev ? {
          ...prev,
          reason: data.reason,
          from: data.date[0].format("YYYY-MM-DD"),
          to: data.date[1].format("YYYY-MM-DD"),
          canEdit: updated.can_edit,
          updatedAt: updated.updated_at,
        } : prev));
      }
      setEditRecord(null);
      return;
    }

    await createLeaveRequest(data);
    message.success("Request submitted");
    await refreshHistory();
  };

  const openEdit = (record) => {
    setOpenDetail(false);
    setEditRecord(record);
    setOpenModal(true);
  };

  const handlePrevWeek = () => {
    const prevWeek = weekOf(currentWeek, currentYear).subtract(1, "week");
    setCurrentWeek(prevWeek.isoWeek());
    setCurrentYear(prevWeek.isoWeekYear());
  };

  const handleNextWeek = () => {
    const nextWeek = weekOf(currentWeek, currentYear).add(1, "week");
    setCurrentWeek(nextWeek.isoWeek());
    setCurrentYear(nextWeek.isoWeekYear());
  };

  const columns = [
    { title: "Type", dataIndex: "type", align: "center" },
    {
      title: "From - To",
      align: "center",
      render: (_, r) => `${r.from} → ${r.to}`,
    },
    {
      title: "Total Hours",
      dataIndex: "hours",
      align: "center",
      render: (h) => `${h}h`,
    },
    {
      title: "Status",
      dataIndex: "status",
      align: "center",
      render: (_, record) => {
        return <StatusPill status={record.workflowStatus || record.status} />;
      },
    },
  ];

  return (
    <div className="page-shell page-shell--three-row">
      <section>
        <h1 className="page-title">Leave Dashboard</h1>
      </section>

      <section className="metric-grid">
        {dashboardMetrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </section>

      <Row gutter={[24, 24]}>
        {/* ================= LEFT ================= */}
        <Col xs={24} lg={16}>
          <Card
            className="office-card table-card"
            title="Leave History"
            extra={
              <div className="toolbar-actions">
                <Select
                  value={sort}
                  onChange={setSort}
                  options={[
                    { value: "new", label: "Newest" },
                    { value: "old", label: "Oldest" },
                  ]}
                />
                <Button
                  type="primary"
                  className="app-button-primary"
                  onClick={() => setOpenModal(true)}
                >
                  + New request
                </Button>
              </div>
            }
          >
            <div className="responsive-desktop-table">
              <Table
                rowKey="id"
                columns={columns}
                dataSource={history}
                loading={loading}
                scroll={{ x: 500 }}
                pagination={{ pageSize: 6 }}
                onRow={(record) => ({
                  onClick: () => {
                    setSelectedRequest(record);
                    setOpenDetail(true);
                  },
                  style: { cursor: "pointer" },
                })}
              />
            </div>
            <div className="responsive-mobile-list">
              <div className="responsive-record-list" aria-live="polite">
                {history.map((request) => (
                  <ResponsiveRecordCard
                    key={request.id}
                    title={request.type}
                    badge={<StatusPill status={request.workflowStatus || request.status} />}
                    onClick={() => {
                      setSelectedRequest(request);
                      setOpenDetail(true);
                    }}
                    ariaLabel={`View ${request.type} request from ${request.from}`}
                  >
                    <ResponsiveRecordRow label="From">{request.from}</ResponsiveRecordRow>
                    <ResponsiveRecordRow label="To">{request.to}</ResponsiveRecordRow>
                    <ResponsiveRecordRow label="Total">{request.hours}h</ResponsiveRecordRow>
                  </ResponsiveRecordCard>
                ))}
                {!loading && history.length === 0 && (
                  <div className="responsive-empty-state">No leave requests found.</div>
                )}
              </div>
            </div>
          </Card>
        </Col>

        {/* ================= RIGHT ================= */}
        <Col xs={24} lg={8}>
          {/* ===== BALANCE ===== */}
          <Card
            className="office-card balance-card"
            title="Your Balance"
          >
            {loading ? (
              <p style={{ textAlign: "center", padding: 20, color: "var(--color-muted)" }}>Loading…</p>
            ) : (
              <div className="balance-stack">
                {balance.map((b) => {
                  return (
                    <BalanceMeter
                      key={b.type}
                      label={b.label}
                      remainingHours={b.remaining_hours}
                      allocatedHours={b.allocated_hours}
                      tone={b.type.includes("VACATION") ? "accent" : "danger"}
                    />
                  );
                })}
              </div>
            )}
          </Card>

          {/* ===== UPCOMING ===== */}
          <Card
            className="office-card events-card"
            title="Upcoming Events"
            extra={
              <div className="events-week-switch">
                <Button type="text" size="small" icon={<LeftOutlined />} onClick={handlePrevWeek} />
                <Text strong className="events-week-switch__label" style={{ fontSize: 13 }}>
                  W{currentWeek}
                </Text>
                <Button type="text" size="small" icon={<RightOutlined />} onClick={handleNextWeek} />
              </div>
            }
          >
            {(() => {
              const weekStart = weekOf(currentWeek, currentYear).startOf("isoWeek");
              const weekEnd = weekOf(currentWeek, currentYear).endOf("isoWeek");

              const startMonth = weekStart.format("MMM");
              const endMonth = weekEnd.format("MMM");
              const startDay = weekStart.format("DD");
              const endDay = weekEnd.format("DD");
              const year = weekEnd.year();

              const dateRange = startMonth === endMonth
                ? `${startMonth} ${startDay} – ${endDay}, ${year}`
                : `${startMonth} ${startDay} – ${endMonth} ${endDay}, ${year}`;

              return (
                <>
                  <div style={{ marginBottom: 12 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dateRange}
                    </Text>
                  </div>
                  {loading ? (
                    <p style={{ textAlign: "center", padding: 20, color: "var(--color-muted)" }}>Loading…</p>
                  ) : upcomingEvents.length === 0 ? (
                    <p style={{ textAlign: "center", padding: 20, color: "var(--color-muted)" }}>
                      No events this week
                    </p>
                  ) : (
                    <div>
                      {upcomingEvents.map((e) => {
                        const style = EVENT_STYLE[e.type];
                        return (
                          <EventCard
                            key={e.id}
                            event={e}
                            styleConfig={style}
                            onClick={() =>
                              navigate("/calendar", {
                                state: { date: e.from, type: e.type, eventId: e.id },
                              })
                            }
                          />
                        );
                      })}
                    </div>
                  )}
                </>
              );
            })()}
          </Card>
        </Col>
      </Row>

      <NewLeaveRequestModal
        open={openModal}
        onCancel={() => {
          setOpenModal(false);
          setEditRecord(null);
        }}
        onSubmit={handleCreateRequest}
        balances={balance}
        mode={editRecord ? "edit" : "create"}
        initialRecord={editRecord}
      />

      <Modal
        open={openDetail}
        onCancel={() => setOpenDetail(false)}
        footer={
          selectedRequest?.canEdit
            ? [
                <Button key="edit" type="primary" onClick={() => openEdit(selectedRequest)}>
                  Edit request
                </Button>,
              ]
            : null
        }
        title="Leave Request Detail"
        width={820}
      >
        {selectedRequest && (
          <>
            <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Type">
              <Tag
                style={
                  selectedRequest.type === "Vacation"
                    ? { color: "var(--color-accent)", background: "var(--color-accent-soft)", border: "1px solid var(--color-accent)" }
                    : selectedRequest.type === "Sick Leave"
                      ? { color: "var(--color-danger)", background: "var(--color-danger-soft)", border: "1px solid var(--color-danger)" }
                      : { color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }
                }
              >
                {selectedRequest.type}
              </Tag>
            </Descriptions.Item>

            <Descriptions.Item label="Date">
              {selectedRequest.from} → {selectedRequest.to}
            </Descriptions.Item>

            {(selectedRequest.startTime || selectedRequest.endTime) && (
              <Descriptions.Item label="Time">
                {selectedRequest.startTime || "--:--"} → {selectedRequest.endTime || "--:--"}
              </Descriptions.Item>
            )}

            <Descriptions.Item label="Total Hours">
              {selectedRequest.hours}h
            </Descriptions.Item>

            <Descriptions.Item label="Status">
              <Tag
                style={
                  selectedRequest.status === "Approved"
                    ? { color: "var(--color-success)", background: "var(--color-success-soft)", border: "1px solid var(--color-success)" }
                    : selectedRequest.status === "Rejected"
                      ? { color: "var(--color-danger)", background: "var(--color-danger-soft)", border: "1px solid var(--color-danger)" }
                      : selectedRequest.currentApprovalStep === "FINAL"
                        ? { color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }
                        : { color: "var(--color-warning)", background: "var(--color-warning-soft)", border: "1px solid var(--color-warning)" }
                }
              >
                {selectedRequest.workflowStatus || selectedRequest.status}
              </Tag>
            </Descriptions.Item>

            {/* ✅ CHỈ HIỆN KHI REJECTED */}
            {selectedRequest.status === "Rejected" &&
              selectedRequest.denyReason && (
                <Descriptions.Item label="Deny Reason">
                  <Text type="danger">{selectedRequest.denyReason}</Text>
                </Descriptions.Item>
              )}

            {selectedRequest.status === "Approved" &&
              selectedRequest.approverComment && (
                <Descriptions.Item label="Approval Note">
                  {selectedRequest.approverComment}
                </Descriptions.Item>
              )}

            {/* ✅ ATTACHMENT */}
            {selectedRequest.attachment && (
              <Descriptions.Item label="Attachment">
                <Space>
                  <PaperClipOutlined />
                  <Text underline>
                    <a
                      href={getMediaUrl(selectedRequest.attachment)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View Attachment
                    </a>
                  </Text>
                </Space>
              </Descriptions.Item>
            )}
            </Descriptions>

            {selectedRequest.approvalTimeline?.length > 0 && (
              <section style={{ marginTop: 20 }}>
                <Text strong style={{ display: "block", marginBottom: 10 }}>
                  Approval progress
                </Text>
                <ApprovalProgress
                  timeline={selectedRequest.approvalTimeline}
                  currentStep={selectedRequest.currentApprovalStep}
                />
              </section>
            )}
          </>
        )}
      </Modal>
    </div>
  );
}
