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
import { PaperClipOutlined } from "@ant-design/icons";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import NewLeaveRequestModal from "@components/NewLeaveRequestModal";
import { PieChart, Pie, Cell, Tooltip } from "recharts";
import { getLeaveHistory, getLeaveBalance, getUpcomingEvents, createLeaveRequest } from "../api/dashboardApi";

const { Text } = Typography;

const EVENT_STYLE = {
  holiday: {
    bg: "#FFF7E6",
    badge: "#FAAD14",
    tag: "gold",
    label: "Holiday",
  },
  PTO: {
    bg: "#F0F5FF",
    badge: "#1677ff",
    tag: "blue",
    label: "PTO",
  },
  business: {
    bg: "#F9F0FF",
    badge: "#722ed1",
    tag: "purple",
    label: "Business Trip",
  },
};

export default function Dashboard() {
  const navigate = useNavigate();

  const [history, setHistory] = useState([]);
  const [balance, setBalance] = useState({ total: 96, used: 0, free: 96 });
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [sort, setSort] = useState("new");
  const [openModal, setOpenModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [openDetail, setOpenDetail] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [historyData, balanceData, eventsData] = await Promise.all([
          getLeaveHistory(sort),
          getLeaveBalance(),
          getUpcomingEvents(),
        ]);
        setHistory(historyData);
        setBalance(balanceData);
        setUpcomingEvents(eventsData);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        message.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [sort]);

  const handleCreateRequest = async (data) => {
    try {
      await createLeaveRequest(data);
      message.success("Request submitted");

      // Refresh data
      const [historyData, balanceData] = await Promise.all([
        getLeaveHistory(sort),
        getLeaveBalance(),
      ]);
      setHistory(historyData);
      setBalance(balanceData);
    } catch (error) {
      // Extract detailed error message
      let errorMsg = "Failed to submit request";
      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMsg = error.response.data;
        } else if (error.response.data.error) {
          errorMsg = error.response.data.error;
        } else if (error.response.data.detail) {
          errorMsg = error.response.data.detail;
        } else if (error.response.data.message) {
          errorMsg = error.response.data.message;
        }
      } else if (error.message) {
        errorMsg = error.message;
      }

      message.error(errorMsg);
    }
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
      render: (s) => {
        const color =
          s === "Approved" ? "green" : s === "Rejected" ? "red" : "orange";
        return <Tag color={color}>{s}</Tag>;
      },
    },
  ];

  const chartData = [
    { name: "Used", value: balance.used },
    { name: "Free", value: balance.free },
  ];

  return (
    <>
      <Row gutter={24}>
        {/* ================= LEFT ================= */}
        <Col span={16}>
          <Card
            title="Leave History"
            extra={
              <>
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
                  style={{ marginLeft: 8 }}
                  onClick={() => setOpenModal(true)}
                >
                  + New request
                </Button>
              </>
            }
            style={{ borderRadius: 16 }}
          >
            <Table
              rowKey="id"
              columns={columns}
              dataSource={history}
              loading={loading}
              pagination={{ pageSize: 6 }}
              onRow={(record) => ({
                onClick: () => {
                  setSelectedRequest(record);
                  setOpenDetail(true);
                },
                style: { cursor: "pointer" },
              })}
            />
          </Card>
        </Col>

        {/* ================= RIGHT ================= */}
        <Col span={8}>
          {/* ===== BALANCE ===== */}
          <Card
            title="Your Balance"
            style={{ borderRadius: 16, marginBottom: 24 }}
          >
            <Row align="middle" gutter={16}>
              {/* CHART */}
              <Col span={10} style={{ textAlign: "center" }}>
                <PieChart width={140} height={140}>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={60}
                  >
                    <Cell fill="#1677ff" />
                    <Cell fill="#91caff" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </Col>

              {/* INFO */}
              <Col span={14}>
                {[
                  {
                    label: "Total",
                    value: balance.total,
                    bg: "#f5f5f5",
                    color: "#000",
                  },
                  {
                    label: "Used",
                    value: balance.used,
                    bg: "rgba(22,119,255,0.15)",
                    color: "#1677ff",
                  },
                  {
                    label: "Free",
                    value: balance.free,
                    bg: "rgba(34, 167, 219, 0.15)",
                    color: "#66c6ecff",
                  },
                ].map((i) => (
                  <div
                    key={i.label}
                    style={{
                      background: i.bg,
                      borderRadius: 10,
                      padding: "8px 12px",
                      fontWeight: 600,
                      color: i.color,
                      marginBottom: 10,
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <span>{i.label}</span>
                    <span>{i.value}h</span>
                  </div>
                ))}
              </Col>
            </Row>
          </Card>

          {/* ===== UPCOMING ===== */}
          <Card title="Upcoming Events" style={{ borderRadius: 16 }}>
            {loading ? (
              <p style={{ textAlign: "center", padding: 20 }}>Loading...</p>
            ) : upcomingEvents.length === 0 ? (
              <p style={{ textAlign: "center", padding: 20, color: "#999" }}>No upcoming events</p>
            ) : (
              upcomingEvents.map((e) => {
              const style = EVENT_STYLE[e.type];
              const date = new Date(e.from);

              return (
                <div
                  key={e.id}
                  onClick={() =>
                    navigate("/calendar", {
                      state: {
                        date: e.from,
                        type: e.type,
                        eventId: e.id,
                      },
                    })
                  }
                  style={{
                    display: "flex",
                    gap: 12,
                    padding: 12,
                    marginBottom: 12,
                    borderRadius: 12,
                    background: style.bg,
                    cursor: "pointer",
                    transition: "0.2s",
                  }}
                >
                  {/* DATE */}
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 10,
                      background: style.badge,
                      color: "#fff",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 600,
                    }}
                  >
                    <div style={{ fontSize: 12 }}>
                      {date.toLocaleString("en", { month: "short" })}
                    </div>
                    <div style={{ fontSize: 16 }}>{date.getDate()}</div>
                  </div>

                  {/* INFO */}
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{e.title}</div>
                    <div style={{ fontSize: 12, color: "#595959" }}>
                      {e.from} → {e.to}
                    </div>
                  </div>

                  <Tag color={style.tag}>{style.label}</Tag>
                </div>
              );
              })
            )}
          </Card>
        </Col>
      </Row>

      <NewLeaveRequestModal
        open={openModal}
        onCancel={() => setOpenModal(false)}
        onSubmit={handleCreateRequest}
      />

      <Modal
        open={openDetail}
        onCancel={() => setOpenDetail(false)}
        footer={null}
        title="Leave Request Detail"
      >
        {selectedRequest && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Type">
              <Tag
                color={
                  selectedRequest.type === "PTO"
                    ? "blue"
                    : selectedRequest.type === "Sick Leave"
                      ? "red"
                      : "purple"
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
                color={
                  selectedRequest.status === "Approved"
                    ? "green"
                    : selectedRequest.status === "Rejected"
                      ? "red"
                      : "orange"
                }
              >
                {selectedRequest.status}
              </Tag>
            </Descriptions.Item>

            {/* ✅ CHỈ HIỆN KHI REJECTED */}
            {selectedRequest.status === "Rejected" &&
              selectedRequest.denyReason && (
                <Descriptions.Item label="Deny Reason">
                  <Text type="danger">{selectedRequest.denyReason}</Text>
                </Descriptions.Item>
              )}

            {/* ✅ ATTACHMENT */}
            {selectedRequest.attachment && (
              <Descriptions.Item label="Attachment">
                <Space>
                  <PaperClipOutlined />
                  <Text underline>
                    <a
                      href={selectedRequest.attachment}
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
        )}
      </Modal>
    </>
  );
}
