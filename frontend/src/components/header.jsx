import {
  Layout,
  Avatar,
  Dropdown,
  Space,
  Badge,
  List,
  Typography,
  Divider,
  Button,
  Empty,
} from "antd";
import {
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  CheckOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "@hooks/use-notifications";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

const { Header } = Layout;

/* ================= NOTIFICATION POPUP ================= */
const NotificationPopup = ({ notifications, markAsRead, markAllAsRead, onNotificationClick }) => {
  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <div
      style={{
        width: 380,
        background: "#fff",
        borderRadius: 8,
        boxShadow: "0 10px 30px rgba(0,0,0,0.15)",
        padding: 12,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 8,
        }}
      >
        <Typography.Text strong>Notifications</Typography.Text>
        {hasUnread && (
          <Button
            type="link"
            size="small"
            icon={<CheckOutlined />}
            onClick={markAllAsRead}
          >
            Mark all read
          </Button>
        )}
      </div>
      <Divider style={{ margin: "8px 0" }} />

      {notifications.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No notifications"
        />
      ) : (
        <List
          itemLayout="horizontal"
          dataSource={notifications}
          renderItem={(item) => (
            <List.Item
              style={{
                padding: "8px",
                cursor: "pointer",
                borderRadius: 6,
                background: item.is_read ? "#fff" : "#f0f7ff",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = "#f5f5f5")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = item.is_read
                  ? "#fff"
                  : "#f0f7ff")
              }
              onClick={() => onNotificationClick(item)}
            >
              <List.Item.Meta
                avatar={
                  <Badge dot={!item.is_read}>
                    <Avatar
                      size={36}
                      icon={<BellOutlined />}
                      style={{ backgroundColor: "#1677ff" }}
                    />
                  </Badge>
                }
                title={
                  <Typography.Text strong={!item.is_read}>
                    {item.title}
                  </Typography.Text>
                }
                description={
                  <>
                    <Typography.Text
                      type="secondary"
                      style={{ fontSize: 12 }}
                    >
                      {item.message}
                    </Typography.Text>
                    <div style={{ fontSize: 11, color: "#999", marginTop: 4 }}>
                      {dayjs(item.created_at).fromNow()}
                    </div>
                  </>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

/* ================= HEADER ================= */
export default function AppHeader() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { notifications, unreadCount, markAsRead, markAllAsRead } =
    useNotifications();

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  const handleNotificationClick = async (notification) => {
    // Mark as read if unread
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }

    // Navigate based on notification type
    if (notification.type === "LEAVE_PENDING") {
      // Approver clicks pending request → navigate to Manager Ticket page
      navigate("/manager");
    } else if (
      (notification.type === "LEAVE_APPROVED" || notification.type === "LEAVE_REJECTED") &&
      notification.related_object_id
    ) {
      // User clicks approved/rejected notification → navigate to dashboard with state
      // Include timestamp to ensure React Router triggers re-render even if same request
      navigate("/dashboard", {
        state: { openRequestId: notification.related_object_id, _ts: Date.now() }
      });
    } else {
      // For other notification types, navigate to dashboard
      navigate("/dashboard");
    }
  };

  const menuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "Profile",
      onClick: () => navigate("/profile"),
    },
    // Only show Settings for HR and Admin
    ...(user?.role === "HR" || user?.role === "ADMIN"
      ? [
          {
            key: "settings",
            icon: <SettingOutlined />,
            label: "Settings",
            onClick: () => navigate("/settings"),
          },
          {
            type: "divider",
          },
        ]
      : []),
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: <span style={{ color: "red" }}>Logout</span>,
      onClick: handleLogout,
    },
  ];

  return (
    <Header
      style={{
        background: "#fff",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        lineHeight: "normal",
        boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
      }}
    >
      {/* LEFT */}
      <h2 style={{ margin: 0 }}>LEAVE MANAGEMENT SYSTEM</h2>

      {/* RIGHT */}
      <Space size={16} align="center">
        {/* USER INFO */}
        <div style={{ textAlign: "right", lineHeight: "18px" }}>
          <div style={{ fontWeight: 600 }}>
            Hello, {user.name || `${user.firstName || ''} ${user.lastName || ''}`.trim()}
          </div>
          <div style={{ fontSize: 12, color: "#888" }}>
            {user.department?.name || user.department} – {user.location?.name || user.location}
          </div>
        </div>

        {/* NOTIFICATION ICON */}
        <Dropdown
          trigger={["click"]}
          dropdownRender={() => (
            <NotificationPopup
              notifications={notifications}
              markAsRead={markAsRead}
              markAllAsRead={markAllAsRead}
              onNotificationClick={handleNotificationClick}
            />
          )}
          placement="bottomRight"
        >
          <Badge count={unreadCount} size="small">
            <BellOutlined
              style={{
                fontSize: 20,
                cursor: "pointer",
                color: "#555",
              }}
            />
          </Badge>
        </Dropdown>

        {/* PROFILE */}
        <Dropdown trigger={["hover"]} menu={{ items: menuItems }}>
          <Avatar
            src={user.avatar}
            size={40}
            style={{ cursor: "pointer" }}
          />
        </Dropdown>
      </Space>
    </Header>
  );
}
