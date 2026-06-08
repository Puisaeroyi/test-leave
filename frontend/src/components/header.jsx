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
  Pagination,
  Spin,
} from "antd";
import {
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  ReadOutlined,
  CheckOutlined,
  CloseOutlined,
  SettingOutlined,
  MenuOutlined,
} from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import { useNavigate } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import { getAnnouncements } from "@api/announcement-api";
import { useNotifications } from "@hooks/use-notification-actions";
import AnnouncementModal from "@components/AnnouncementModal";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

const { Header } = Layout;
const ANNOUNCEMENT_PAGE_SIZE = 5;

const AnnouncementDropdown = ({
  announcements,
  count,
  loading,
  onAnnouncementClick,
  onPageChange,
  page,
  pageSize,
  isMobile,
}) => (
  <div
    className="notification-popup"
    style={{
      width: isMobile ? "calc(100vw - 32px)" : 380,
      maxWidth: 380,
      padding: 12,
    }}
  >
    <Typography.Text strong style={{ color: "var(--color-text)" }}>
      Announcements
    </Typography.Text>
    <Divider style={{ margin: "8px 0" }} />

    <Spin spinning={loading}>
      {announcements.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No announcements" />
      ) : (
        <>
          <List
            itemLayout="horizontal"
            dataSource={announcements}
            renderItem={(item) => (
              <List.Item
                className="notification-item"
                onClick={() => onAnnouncementClick(item)}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar
                      size={36}
                      icon={<ReadOutlined />}
                      style={{ backgroundColor: "var(--color-accent-strong)" }}
                    />
                  }
                  title={<Typography.Text strong>{item.title}</Typography.Text>}
                  description={
                    <>
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        {item.body.length > 96 ? `${item.body.slice(0, 96)}...` : item.body}
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
          {count > pageSize && (
            <Pagination
              align="end"
              current={page}
              pageSize={pageSize}
              total={count}
              onChange={onPageChange}
              showSizeChanger={false}
              size="small"
              style={{ marginTop: 8 }}
            />
          )}
        </>
      )}
    </Spin>
  </div>
);

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
  const [autoOpenAnnouncements, setAutoOpenAnnouncements] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [announcementCount, setAnnouncementCount] = useState(0);
  const [announcementPage, setAnnouncementPage] = useState(1);
  const [announcementsLoading, setAnnouncementsLoading] = useState(false);
  // Modal is driven by an array + index so both the login stepper (many) and a
  // dropdown click (single) share one code path; nav shows only when length > 1.
  const [modalAnnouncements, setModalAnnouncements] = useState([]);
  const [modalIndex, setModalIndex] = useState(0);
  const [announcementsOpen, setAnnouncementsOpen] = useState(false);
  const { notifications, unreadCount, markAsRead, markAllAsRead, dismissNotification, dismissAll } =
    useNotifications();

  const fetchAutoOpenAnnouncements = useCallback(async () => {
    try {
      const data = await getAnnouncements({ page: 1, page_size: 20 });
      setAutoOpenAnnouncements(data.results || []);
      setAnnouncementCount(data.count || 0);
    } catch (error) {
      console.error("Failed to fetch announcements:", error);
    }
  }, []);

  const fetchAnnouncementPage = useCallback(async (page = 1) => {
    setAnnouncementsLoading(true);
    try {
      const data = await getAnnouncements({ page, page_size: ANNOUNCEMENT_PAGE_SIZE });
      setAnnouncements(data.results || []);
      setAnnouncementCount(data.count || 0);
      setAnnouncementPage(page);
    } catch (error) {
      console.error("Failed to fetch announcements:", error);
    } finally {
      setAnnouncementsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    fetchAutoOpenAnnouncements();
  }, [fetchAutoOpenAnnouncements, user]);

  useEffect(() => {
    if (!user || autoOpenAnnouncements.length === 0) return;

    // Dedupe on the newest announcement id: re-pop only when something new appears.
    const newestId = autoOpenAnnouncements[0].id;
    const storageKey = `announcements:auto-opened:${user.id}`;
    if (sessionStorage.getItem(storageKey) === newestId) return;

    setModalAnnouncements(autoOpenAnnouncements);
    setModalIndex(0);
    setAnnouncementsOpen(true);
    sessionStorage.setItem(storageKey, newestId);
  }, [autoOpenAnnouncements, user]);

  const openAnnouncementDropdown = () => {
    fetchAnnouncementPage(1);
  };

  const handleAnnouncementClick = (announcement) => {
    setModalAnnouncements([announcement]);
    setModalIndex(0);
    setAnnouncementsOpen(true);
  };

  const handleAnnouncementPrev = () =>
    setModalIndex((i) => Math.max(0, i - 1));
  const handleAnnouncementNext = () =>
    setModalIndex((i) => Math.min(modalAnnouncements.length - 1, i + 1));

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

        {/* ANNOUNCEMENT ICON */}
        <Dropdown
          trigger={["click"]}
          onOpenChange={(open) => {
            if (open) openAnnouncementDropdown();
          }}
          dropdownRender={() => (
            <AnnouncementDropdown
              announcements={announcements}
              count={announcementCount}
              loading={announcementsLoading}
              onAnnouncementClick={handleAnnouncementClick}
              onPageChange={fetchAnnouncementPage}
              page={announcementPage}
              pageSize={ANNOUNCEMENT_PAGE_SIZE}
              isMobile={isMobile}
            />
          )}
          placement="bottomRight"
        >
          <Badge dot={announcementCount > 0} size="small">
            <button
              type="button"
              className="header-icon-button"
              aria-label="Open announcements"
            >
              <ReadOutlined style={{ fontSize: 18 }} />
            </button>
          </Badge>
        </Dropdown>

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
      <AnnouncementModal
        announcement={modalAnnouncements[modalIndex] || null}
        index={modalIndex}
        total={modalAnnouncements.length}
        onPrev={handleAnnouncementPrev}
        onNext={handleAnnouncementNext}
        open={announcementsOpen}
        onClose={() => setAnnouncementsOpen(false)}
      />
    </Header>
  );
}
