// components/CreateEventModal.jsx
// Type selector modal: routes to Leave Request or Business Trip creation
// allowLeave=false hides the leave option (e.g. when selected date is within 3 days)
import { Modal, Card, Space, Typography, Tooltip } from "antd";

const { Title, Text } = Typography;

export default function CreateEventModal({ open, onClose, onSelect, allowLeave = true }) {
  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={520}
      title="Create new request"
      destroyOnClose
    >
      <Space direction="vertical" style={{ width: "100%" }} size={16}>
        {allowLeave ? (
          <Card
            hoverable
            onClick={() => onSelect("leave")}
            style={{ borderLeft: "5px solid #1677ff" }}
          >
            <Title level={5}>Leave Request</Title>
            <Text type="secondary">
              Vacation, Sick leave, Hour-based leave
            </Text>
          </Card>
        ) : (
          <Tooltip title="Leave requests must be submitted at least 3 days in advance">
            <Card
              style={{
                borderLeft: "5px solid #d9d9d9",
                opacity: 0.45,
                cursor: "not-allowed",
              }}
            >
              <Title level={5} type="secondary">Leave Request</Title>
              <Text type="secondary">
                Requires at least 3 days advance notice
              </Text>
            </Card>
          </Tooltip>
        )}

        <Card
          hoverable
          onClick={() => onSelect("business")}
          style={{ borderLeft: "5px solid #722ed1" }}
        >
          <Title level={5}>Business Trip</Title>
          <Text type="secondary">
            Company-sponsored travel
          </Text>
        </Card>
      </Space>
    </Modal>
  );
}
