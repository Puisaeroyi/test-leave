import {
  Layout,
  Avatar,
  Dropdown,
  Space,
  Badge,
  List,
  Typography,
  Divider,
} from "antd";
import {
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import { useNavigate } from "react-router-dom";

const { Header } = Layout;

/* ================= MOCK NOTIFICATION DATA ================= */
const notifications = [
  {
    id: 1,
    title: "Leave request approved",
    description: "Your PTO request (Feb 20 → Feb 21) was approved",
    time: "2 hours ago",
    read: false,
  },
  {
    id: 2,
    title: "New company announcement",
    description: "Company meeting on Friday at 3PM",
    time: "Yesterday",
    read: true,
  },
  {
    id: 3,
    title: "Leave request pending",
    description: "Your sick leave request is pending approval",
    time: "2 days ago",
    read: true,
  },
];

/* ================= NOTIFICATION POPUP ================= */
const NotificationPopup = () => (
  <div
    style={{
      width: 340,
      background: "#fff",
      borderRadius: 8,
      boxShadow: "0 10px 30px rgba(0,0,0,0.15)",
      padding: 12,
    }}
  >
    <Typography.Text strong>Notifications</Typography.Text>
    <Divider style={{ margin: "8px 0" }} />

    <List
      itemLayout="horizontal"
      dataSource={notifications}
      locale={{ emptyText: "No notifications" }}
      renderItem={(item) => (
        <List.Item
          style={{
            padding: "8px",
            cursor: "pointer",
            borderRadius: 6,
            background: item.read ? "#fff" : "#f0f7ff",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "#f5f5f5")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = item.read
              ? "#fff"
              : "#f0f7ff")
          }
        >
          <List.Item.Meta
            avatar={
              <Badge dot={!item.read}>
                <Avatar
                  size={36}
                  icon={<BellOutlined />}
                  style={{ backgroundColor: "#1677ff" }}
                />
              </Badge>
            }
            title={
              <Typography.Text strong={!item.read}>
                {item.title}
              </Typography.Text>
            }
            description={
              <>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {item.description}
                </Typography.Text>
                <div style={{ fontSize: 11, color: "#999", marginTop: 4 }}>
                  {item.time}
                </div>
              </>
            }
          />
        </List.Item>
      )}
    />
  </div>
);

/* ================= HEADER ================= */
export default function AppHeader() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  const menuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "Profile",
      onClick: () => navigate("/profile"),
    },
    {
      type: "divider",
    },
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
          dropdownRender={() => <NotificationPopup />}
          placement="bottomRight"
        >
          <Badge
            count={notifications.filter((n) => !n.read).length}
            size="small"
          >
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
