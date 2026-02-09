import { Layout, Menu, ConfigProvider } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@auth/authContext";
import {
  DashboardOutlined,
  CalendarOutlined,
  TeamOutlined,
  RocketOutlined,
  SendOutlined,
} from "@ant-design/icons";
import logo from "@/assets/logo.png";

const { Sider } = Layout;

export default function Sidebar() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!user) return null;

  const items = [
    {
      key: "/dashboard",
      icon: <DashboardOutlined />,
      label: "Dashboard",
    },
    {
      key: "/calendar",
      icon: <CalendarOutlined />,
      label: "Team Calendar",
    },
    {
      key: "/business-trip",
      icon: <RocketOutlined />,
      label: "Business Trip",
    },
  ];

  if (user.role === "MANAGER" || user.role === "HR" || user.role === "ADMIN" || user.isApprover) {
    items.push({
      key: "/manager",
      icon: <TeamOutlined />,
      label: "Manager Ticket",
    });
    items.push({
      key: "/business-trip-tickets",
      icon: <SendOutlined />,
      label: "Business Trip Ticket",
    });
  }

  return (
    <Sider
      width={220}
      style={{
        background: "#576A8F",
      }}
    >
      {/* LOGO */}
      <div
        style={{
          height: 64,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#4A5C80",
        }}
      >
        <img
          src={logo}
          alt="logo"
          style={{
            height: 36,
            objectFit: "contain",
          }}
        />
      </div>

      {/* MENU */}
      <ConfigProvider
        theme={{
          components: {
            Menu: {
              itemBg: "#576A8F",
              itemColor: "#FFFFFF",
              itemHoverBg: "#FFF8DE",
              itemHoverColor: "#000000",
              itemSelectedBg: "#FFF8DE",
              itemSelectedColor: "#000000",
              iconColor: "#FFFFFF",
              iconHoverColor: "#000000",
              iconSelectedColor: "#000000",
            },
          },
        }}
      >
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={items}
          onClick={({ key }) => navigate(key)}
          style={{
            background: "#576A8F",
            borderRight: "none",
          }}
        />
      </ConfigProvider>
    </Sider>
  );
}
