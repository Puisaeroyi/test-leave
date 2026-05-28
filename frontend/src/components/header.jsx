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
  CloseOutlined,
  SettingOutlined,
  MenuOutlined,
} from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "@hooks/use-notification-actions";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

const { Header } = Layout;

/* ================= NOTIFICATION POPUP ================= */
const NotificationPopup = ({ notifications, markAllAsRead, onNotificationClick, dismissNotification, dismissAll, isMobile }) => {
  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <div
      className="notification-popup"
      style={{
        width: isMobile ? "calc(100vw - 32px)" : 380,
        maxWidth: 380,
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
        <Typography.Text strong style={{ color: "var(--color-text)" }}>
          Notifications
        </Typography.Text>
        <Space size={4} wrap>
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
          {notifications.length > 0 && (
            <Button
              type="link"
              size="small"
              icon={<CloseOutlined />}
              onClick={dismissAll}
              style={{ color: "var(--color-muted)" }}
            >
              Dismiss all
            </Button>
          )}
        </Space>
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
              className={`notification-item${item.is_read ? "" : " notification-item--unread"}`}
              onClick={() => onNotificationClick(item)}
              extra={
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    dismissNotification(item.id);
                  }}
                  style={{ color: "var(--color-muted)", fontSize: 12 }}
                />
              }
            >
              <List.Item.Meta
                avatar={
                  <Badge dot={!item.is_read}>
                    <Avatar
                      size={36}
                      icon={<BellOutlined />}
                      style={{ backgroundColor: "var(--color-accent-strong)" }}
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
                    <div style={{ fontSize: 11, color: "var(--color-muted)", marginTop: 4 }}>
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
export default function AppHeader({ isMobile, onMenuClick }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { notifications, unreadCount, markAsRead, markAllAsRead, dismissNotification, dismissAll } =
    useNotifications();

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }

    if (notification.type === "LEAVE_PENDING") {
      navigate("/manager");
    } else if (
      (notification.type === "LEAVE_APPROVED" || notification.type === "LEAVE_REJECTED") &&
      notification.related_object_id
    ) {
      navigate("/dashboard", {
        state: { openRequestId: notification.related_object_id, _ts: Date.now() }
      });
    } else {
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
      label: <span style={{ color: "var(--color-danger)" }}>Logout</span>,
      onClick: handleLogout,
    },
  ];

  return (
    <Header
      className="app-header"
    >
      {/* LEFT */}
      <div className="header-left">
        {isMobile && (
          <button
            type="button"
            className="header-menu-button"
            aria-label="Open navigation menu"
            onClick={onMenuClick}
          >
            <MenuOutlined style={{ fontSize: 18 }} />
          </button>
        )}
        <div>
          {!isMobile && <div className="header-title-kicker"></div>}
          <h2 className="header-title">
            {isMobile ? "LMS" : "Leave Management System"}
          </h2>
        </div>
      </div>

      {/* RIGHT */}
      <Space size={isMobile ? 8 : 16} align="center">
        {/* USER INFO - hidden on mobile */}
        {!isMobile && (
          <div className="header-user">
            <div className="header-user__name">
              Hello, {user.name || `${user.firstName || ''} ${user.lastName || ''}`.trim()}
            </div>
            <div className="header-user__meta">
              {user.department?.name || user.department} – {user.location?.name || user.location}
            </div>
          </div>
        )}

        {/* NOTIFICATION ICON */}
        <Dropdown
          trigger={["click"]}
          dropdownRender={() => (
            <NotificationPopup
              notifications={notifications}
              markAllAsRead={markAllAsRead}
              onNotificationClick={handleNotificationClick}
              dismissNotification={dismissNotification}
              dismissAll={dismissAll}
              isMobile={isMobile}
            />
          )}
          placement="bottomRight"
        >
          <Badge count={unreadCount} size="small">
            <button
              type="button"
              className="header-icon-button"
              aria-label="Open notifications"
            >
              <BellOutlined style={{ fontSize: 18 }} />
            </button>
          </Badge>
        </Dropdown>

        {/* PROFILE */}
        <Dropdown trigger={["click"]} menu={{ items: menuItems }}>
          <Avatar
            src={user.avatar}
            size={isMobile ? 32 : 40}
            aria-label="Open profile menu"
            style={{ cursor: "pointer", background: "var(--color-accent-soft)", border: "1px solid var(--color-border)" }}
          />
        </Dropdown>
      </Space>
    </Header>
  );
}
