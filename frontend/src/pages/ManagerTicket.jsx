import { useState, useEffect, useCallback } from "react";
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
import { getMediaUrl } from "../api/http";
import ApprovalProgress from "../components/ApprovalProgress";

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
    // Pending tickets can only be handled by the approver assigned to the current step.
    if (ticket.status === "Pending") return ticket.actionRequired;
    // Approved tickets can be denied only if within 24h of start
    if (ticket.status === "Approved" && ticket.canManageApproved) {
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

  const fetchPendingRequests = useCallback(async () => {
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
  }, []);

  // Fetch pending requests on mount
  useEffect(() => {
    fetchPendingRequests();
  }, [fetchPendingRequests]);

  const tagStyles = {
    Vacation: {
      color: "var(--color-accent)",
      background: "var(--color-accent-soft)",
      border: "1px solid var(--color-accent)",
    },
    "Sick Leave": {
      color: "var(--color-danger)",
      background: "var(--color-danger-soft)",
      border: "1px solid var(--color-danger)",
    },
    "Business Trip": {
      color: "var(--color-info)",
      background: "var(--color-info-soft)",
      border: "1px solid var(--color-info)",
    },
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
      render: (t) => <Tag style={tagStyles[t]}>{t}</Tag>,
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
      render: (_, record) => {
        const displayStatus = record.workflowStatus || record.status;
        const statusStyle = record.status === "Approved"
          ? { color: "var(--color-success)", background: "var(--color-success-soft)", border: "1px solid var(--color-success)" }
          : record.status === "Denied"
            ? { color: "var(--color-danger)", background: "var(--color-danger-soft)", border: "1px solid var(--color-danger)" }
            : record.actionRequired
              ? { color: "var(--color-warning)", background: "var(--color-warning-soft)", border: "1px solid var(--color-warning)" }
              : { color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" };

        return <Tag style={statusStyle}>{displayStatus}</Tag>;
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
      const result = await approveLeaveRequest(selectedTicket.id, approveReason);
      message.success(
        result.status === "PENDING"
          ? "First approval recorded. Waiting for final approval."
          : "Leave request fully approved."
      );

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
    <div className="page-shell">
      <section>
        <div className="page-kicker">Manager Review</div>
        <h1 className="page-title">Manager Reviews</h1>
        <p className="page-subtitle">
          Review leave requests with clear timing, attachments, and notes for each decision.
        </p>
      </section>

      <Card
        className="page-panel table-card"
        title="Team Leave Requests"
        extra={
          <Space>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 210 }}
              options={[
                { value: "all", label: "All Status" },
                { value: "action-required", label: "Action Required" },
                { value: "Awaiting Final Approval", label: "Awaiting Final Approval" },
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
          dataSource={
            statusFilter === "all"
              ? tickets
              : tickets.filter((ticket) => (
                  statusFilter === "action-required"
                    ? ticket.actionRequired
                    : (ticket.workflowStatus || ticket.status) === statusFilter
                ))
          }
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
        width={820}
        title="Request Detail"
      >
        {selectedTicket && (
          <>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Employee">
                {selectedTicket.employeeName}
              </Descriptions.Item>

              <Descriptions.Item label="Leave Category">
                <Tag style={tagStyles[selectedTicket.type]}>
                  {selectedTicket.type}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Status">
                <Tag
                  style={
                    selectedTicket.status === "Approved"
                      ? { color: "var(--color-success)", background: "var(--color-success-soft)", border: "1px solid var(--color-success)" }
                      : selectedTicket.status === "Denied"
                        ? { color: "var(--color-danger)", background: "var(--color-danger-soft)", border: "1px solid var(--color-danger)" }
                        : selectedTicket.actionRequired
                          ? { color: "var(--color-warning)", background: "var(--color-warning-soft)", border: "1px solid var(--color-warning)" }
                          : { color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }
                  }
                >
                  {selectedTicket.workflowStatus || selectedTicket.status}
                </Tag>
              </Descriptions.Item>

              {/* Time Remaining for Approved tickets */}
              {selectedTicket.status === "Approved" && selectedTicket.canManageApproved && timeInfo && (
                <Descriptions.Item label="Denial Window">
                  <Space>
                    <ClockCircleOutlined style={{
                      color: timeInfo.canDeny ? "var(--color-success)" : "var(--color-danger)"
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
                        href={getMediaUrl(selectedTicket.attachment)}
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

            {selectedTicket.approvalTimeline?.length > 0 && (
              <section style={{ marginTop: 20 }}>
                <Text strong style={{ display: "block", marginBottom: 10 }}>
                  Approval progress
                </Text>
                <ApprovalProgress
                  timeline={selectedTicket.approvalTimeline}
                  currentStep={selectedTicket.currentApprovalStep}
                  actionRequired={selectedTicket.actionRequired}
                />
              </section>
            )}

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
              <Tooltip
                title={
                  selectedTicket.status === "Pending" && !selectedTicket.actionRequired
                    ? "This request is waiting for the final approver."
                    : selectedTicket.status === "Approved" && !canAct
                      ? "Cannot deny within 24h of leave start"
                      : ""
                }
              >
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
              <Tooltip title={!selectedTicket.actionRequired && selectedTicket.status === "Pending" ? "Your approval step is complete." : ""}>
                <Button
                  size="large"
                  disabled={selectedTicket.status !== "Pending" || !selectedTicket.actionRequired}
                  icon={<CheckCircleOutlined />}
                  style={{
                    minWidth: 140,
                    height: 44,
                    fontWeight: 600,
                    background: "var(--color-success)",
                    borderColor: "var(--color-success)",
                    color: "var(--color-on-accent)",
                    opacity: selectedTicket.status === "Pending" && selectedTicket.actionRequired ? 1 : 0.5,
                  }}
                  onClick={() => setConfirmType("approve")}
                >
                  Approve
                </Button>
              </Tooltip>
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
    </div>
  );
}
