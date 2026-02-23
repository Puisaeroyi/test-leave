import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Tag,
  Button,
  Modal,
  Descriptions,
  Space,
  Typography,
  Divider,
  Input,
  message,
  Tooltip,
  Select,
} from "antd";
import {
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PaperClipOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { getPendingRequests, approveLeaveRequest, rejectLeaveRequest } from "../api/dashboardApi";

const { Text } = Typography;
const { TextArea } = Input;

export default function ManagerTickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [confirmType, setConfirmType] = useState(null); // approve | deny
  const [denyReason, setDenyReason] = useState("");
  const [approveReason, setApproveReason] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Check if ticket can be acted upon
  const canActOnTicket = (ticket) => {
    if (!ticket) return false;
    // Pending tickets can always be approved/denied
    if (ticket.status === "Pending") return true;
    // Approved tickets can be denied only if within 24h of start
    if (ticket.status === "Approved") {
      const now = dayjs();
      const leaveStart = dayjs(ticket.from).startOf("day");
      const cutoff = leaveStart.subtract(24, "hour");
      return now.isBefore(cutoff);
    }
    return false;
  };

  // Calculate time remaining for approved tickets
  const getTimeRemaining = (ticket) => {
    if (ticket.status !== "Approved") return null;
    const now = dayjs();
    const leaveStart = dayjs(ticket.from).startOf("day");
    const cutoff = leaveStart.subtract(24, "hour");
    const diff = cutoff.diff(now, "hour");

    if (diff <= 0) return { canDeny: false, text: "Too late to deny" };

    const days = Math.floor(diff / 24);
    const hours = diff % 24;
    let text = "";
    if (days > 0) text += `${days}d `;
    text += `${hours}h`;
    return { canDeny: true, text: `${text} remaining to deny` };
  };

  // Fetch pending requests on mount
  useEffect(() => {
    fetchPendingRequests();
  }, []);

  const fetchPendingRequests = async () => {
    try {
      setLoading(true);
      const data = await getPendingRequests();
      setTickets(data);
    } catch (error) {
      console.error("Failed to fetch pending requests:", error);
      message.error("Failed to load pending requests");
    } finally {
      setLoading(false);
    }
  };

  const typeColor = {
    Vacation: "blue",
    "Sick Leave": "red",
    "Business Trip": "purple",
  };

  // =======================
  // TABLE
  // =======================
  const columns = [
    {
      title: "Employee",
      dataIndex: "employeeName",
      align: "center",
      render: (v) => <Text strong>{v}</Text>,
    },
    {
      title: "Leave Category",
      dataIndex: "type",
      align: "center",
      render: (t) => <Tag color={typeColor[t]}>{t}</Tag>,
    },
    {
      title: "Leave Type",
      dataIndex: "exemptType",
      align: "center",
      render: (t) => <Tag color={t === "Exempt" ? "geekblue" : "cyan"}>{t}</Tag>,
    },
    {
      title: "From - To",
      align: "center",
      render: (_, r) => `${r.from} → ${r.to}`,
    },
    {
      title: "Hours",
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
          s === "Approved" ? "green" : s === "Denied" ? "red" : "orange";

        return <Tag color={color}>{s}</Tag>;
      },
    },
    {
      title: "Action",
      align: "center",
      render: (_, record) => (
        <Button
          type="primary"
          ghost
          icon={<EyeOutlined />}
          onClick={() => setSelectedTicket(record)}
        >
          View detail
        </Button>
      ),
    },
  ];

  // =======================
  // HANDLERS (API INTEGRATION)
  // =======================
  const handleApprove = async () => {
    try {
      setActionLoading(true);
      await approveLeaveRequest(selectedTicket.id, approveReason);
      message.success("Ticket approved");

      // Refresh the list
      await fetchPendingRequests();

      setConfirmType(null);
      setSelectedTicket(null);
      setApproveReason("");
    } catch (error) {
      console.error("Failed to approve:", error);
      let errorMsg = "Failed to approve request";
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      message.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeny = async () => {
    if (!denyReason.trim()) {
      message.warning("Please enter deny reason");
      return;
    }

    if (denyReason.length < 10) {
      message.warning("Deny reason must be at least 10 characters");
      return;
    }

    try {
      setActionLoading(true);
      await rejectLeaveRequest(selectedTicket.id, denyReason);
      message.success("Ticket denied");

      // Refresh the list
      await fetchPendingRequests();

      setConfirmType(null);
      setSelectedTicket(null);
      setDenyReason("");
    } catch (error) {
      console.error("Failed to deny:", error);
      let errorMsg = "Failed to deny request";
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      message.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  const timeInfo = selectedTicket ? getTimeRemaining(selectedTicket) : null;
  const canAct = selectedTicket ? canActOnTicket(selectedTicket) : false;

  return (
    <>
      <Card
        title="📝 Manager – Leave Requests"
        style={{ borderRadius: 16 }}
        extra={
          <Space>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 160 }}
              options={[
                { value: "all", label: "All Status" },
                { value: "Pending", label: "Pending" },
                { value: "Approved", label: "Approved" },
                { value: "Denied", label: "Denied" },
              ]}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchPendingRequests}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={statusFilter === "all" ? tickets : tickets.filter((t) => t.status === statusFilter)}
          rowKey="id"
          loading={loading}
          pagination={false}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* =======================
          DETAIL MODAL (Shared)
      ======================= */}
      <Modal
        open={!!selectedTicket}
        onCancel={() => setSelectedTicket(null)}
        footer={null}
        width={600}
        title="Ticket Detail"
      >
        {selectedTicket && (
          <>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Employee">
                {selectedTicket.employeeName}
              </Descriptions.Item>

              <Descriptions.Item label="Leave Category">
                <Tag color={typeColor[selectedTicket.type]}>
                  {selectedTicket.type}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Leave Type">
                <Tag color={selectedTicket.exemptType === "Exempt" ? "geekblue" : "cyan"}>
                  {selectedTicket.exemptType}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Status">
                <Tag
                  color={
                    selectedTicket.status === "Approved"
                      ? "green"
                      : selectedTicket.status === "Denied"
                        ? "red"
                        : "orange"
                  }
                >
                  {selectedTicket.status}
                </Tag>
              </Descriptions.Item>

              {/* Approver Comment (for approved tickets) */}
              {selectedTicket.status === "Approved" && selectedTicket.approverComment && (
                <Descriptions.Item label="Approver Note">
                  <Text type="secondary">{selectedTicket.approverComment}</Text>
                </Descriptions.Item>
              )}

              {/* Time Remaining for Approved tickets */}
              {selectedTicket.status === "Approved" && timeInfo && (
                <Descriptions.Item label="Denial Window">
                  <Space>
                    <ClockCircleOutlined style={{
                      color: timeInfo.canDeny ? "#52c41a" : "#ff4d4f"
                    }} />
                    <Text type={timeInfo.canDeny ? "success" : "danger"}>
                      {timeInfo.text}
                    </Text>
                  </Space>
                </Descriptions.Item>
              )}

              {selectedTicket.status === "Denied" &&
                selectedTicket.denyReason && (
                  <Descriptions.Item label="Deny Reason">
                    <Text type="danger">{selectedTicket.denyReason}</Text>
                  </Descriptions.Item>
                )}

              <Descriptions.Item label="Date">
                {selectedTicket.from} → {selectedTicket.to}
              </Descriptions.Item>

              {(selectedTicket.startTime || selectedTicket.endTime) && (
                <Descriptions.Item label="Time">
                  {selectedTicket.startTime || "--:--"} → {selectedTicket.endTime || "--:--"}
                </Descriptions.Item>
              )}

              <Descriptions.Item label="Hours">
                {selectedTicket.hours}h
              </Descriptions.Item>

              <Descriptions.Item label="Reason">
                {selectedTicket.reason}
              </Descriptions.Item>

              {selectedTicket.attachment && (
                <Descriptions.Item label="Attachment">
                  <Space>
                    <PaperClipOutlined />
                    <Text underline>
                      <a
                        href={selectedTicket.attachment}
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

            <Divider />

            <Space
              size={24}
              style={{
                width: "100%",
                justifyContent: "center",
                marginTop: 12,
              }}
            >
              {/* Deny button - enabled for Pending and Approved (within 24h) */}
              <Tooltip title={selectedTicket.status === "Approved" && !canAct ? "Cannot deny within 24h of leave start" : ""}>
                <Button
                  size="large"
                  danger
                  disabled={!canAct}
                  icon={<CloseCircleOutlined />}
                  style={{
                    minWidth: 140,
                    height: 44,
                    fontWeight: 600,
                    opacity: canAct ? 1 : 0.5,
                  }}
                  onClick={() => setConfirmType("deny")}
                >
                  Deny
                </Button>
              </Tooltip>

              {/* Approve button - only for Pending tickets */}
              <Button
                size="large"
                disabled={selectedTicket.status !== "Pending"}
                icon={<CheckCircleOutlined />}
                style={{
                  minWidth: 140,
                  height: 44,
                  fontWeight: 600,
                  background: "#52c41a",
                  borderColor: "#52c41a",
                  color: "#fff",
                  opacity: selectedTicket.status === "Pending" ? 1 : 0.5,
                }}
                onClick={() => setConfirmType("approve")}
              >
                Approve
              </Button>
            </Space>
          </>
        )}
      </Modal>

      {/* =======================
          CONFIRM MODAL
      ======================= */}
      <Modal
        open={!!confirmType}
        onCancel={() => setConfirmType(null)}
        onOk={confirmType === "approve" ? handleApprove : handleDeny}
        okText={confirmType === "approve" ? "Approve" : "Deny"}
        confirmLoading={actionLoading}
        okButtonProps={{
          danger: confirmType === "deny",
        }}
        title={confirmType === "approve" ? "Confirm Approve" : "Confirm Deny"}
      >
        {confirmType === "approve" && (
          <>
            <Text>Are you sure you want to approve this ticket?</Text>
            <div style={{ marginTop: 12 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                (Optional) Add a note for the employee:
              </Text>
              <TextArea
                rows={3}
                value={approveReason}
                onChange={(e) => setApproveReason(e.target.value)}
                placeholder="Enter approval note (optional)..."
                style={{ marginTop: 8 }}
                maxLength={500}
                showCount
              />
            </div>
          </>
        )}

        {confirmType === "deny" && (
          <>
            <Text>
              {selectedTicket?.status === "Approved"
                ? "This ticket is already approved. Denying it will restore the employee's balance."
                : "Please provide reason for denying this ticket:"}
            </Text>
            <TextArea
              rows={4}
              value={denyReason}
              onChange={(e) => setDenyReason(e.target.value)}
              placeholder="Enter deny reason (min 10 characters)..."
              style={{ marginTop: 12 }}
            />
          </>
        )}
      </Modal>
    </>
  );
}
