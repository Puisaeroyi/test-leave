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
} from "antd";
import {
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PaperClipOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
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
  const isPending = selectedTicket?.status === "Pending";

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
    PTO: "blue",
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
      title: "Leave Type",
      dataIndex: "type",
      align: "center",
      render: (t) => <Tag color={typeColor[t]}>{t}</Tag>,
    },
    {
      title: "From - To",
      align: "center",
      render: (_, r) => `${r.from} → ${r.to}`,
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
      await approveLeaveRequest(selectedTicket.id);
      message.success("Ticket approved");

      // Refresh the list
      await fetchPendingRequests();

      setConfirmType(null);
      setSelectedTicket(null);
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

  return (
    <>
      <Card
        title="📝 Manager Ticket Approval"
        style={{ borderRadius: 16 }}
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchPendingRequests}
            loading={loading}
          >
            Refresh
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tickets}
          rowKey="id"
          loading={loading}
          pagination={false}
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

              <Descriptions.Item label="Leave Type">
                <Tag color={typeColor[selectedTicket.type]}>
                  {selectedTicket.type}
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
              <Button
                size="large"
                danger
                disabled={!isPending}
                icon={<CloseCircleOutlined />}
                style={{
                  minWidth: 140,
                  height: 44,
                  fontWeight: 600,
                  opacity: isPending ? 1 : 0.5,
                }}
                onClick={() => setConfirmType("deny")}
              >
                Deny
              </Button>

              <Button
                size="large"
                disabled={!isPending}
                icon={<CheckCircleOutlined />}
                style={{
                  minWidth: 140,
                  height: 44,
                  fontWeight: 600,
                  background: "#52c41a",
                  borderColor: "#52c41a",
                  color: "#fff",
                  opacity: isPending ? 1 : 0.5,
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
          <Text>Are you sure you want to approve this ticket?</Text>
        )}

        {confirmType === "deny" && (
          <>
            <Text>Please provide reason for denying this ticket:</Text>
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
