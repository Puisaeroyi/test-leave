import { Layout, Menu, ConfigProvider, Drawer, Grid } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@auth/authContext";
import {
  DashboardOutlined,
  CalendarOutlined,
  TeamOutlined,
  RocketOutlined,
  SendOutlined,
  CustomerServiceOutlined,
} from "@ant-design/icons";
import logo from "@/assets/logo.png";

const { Sider } = Layout;
const { useBreakpoint } = Grid;

// Menu theme config shared between Sider and Drawer
const menuTheme = {
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
};

export default function Sidebar({ mobileOpen, onMobileClose }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();

  // Mobile = below md (< 768px)
  const isMobile = !screens.md;

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

  // Support link - always at the bottom
  items.push({
    key: "/support",
    icon: <CustomerServiceOutlined />,
    label: "Support",
  });

  const handleMenuClick = ({ key }) => {
    navigate(key);
    if (isMobile) onMobileClose?.();
  };

  const logoBlock = (
    <div
      style={{
        height: 64,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#4A5C80",
        cursor: "pointer",
      }}
      onClick={() => {
        navigate("/dashboard");
        if (isMobile) onMobileClose?.();
      }}
    >
      <img
        src={logo}
        alt="logo"
        style={{ height: 36, objectFit: "contain" }}
      />
    </div>
  );

  const menuBlock = (
    <ConfigProvider theme={menuTheme}>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={items}
        onClick={handleMenuClick}
        style={{
          background: "#576A8F",
          borderRight: "none",
        }}
      />
    </ConfigProvider>
  );

  // Mobile: render as Drawer overlay
  if (isMobile) {
    return (
      <Drawer
        placement="left"
        open={mobileOpen}
        onClose={onMobileClose}
        width={220}
        styles={{ body: { padding: 0, background: "#576A8F" } }}
        closable={false}
      >
        {logoBlock}
        {menuBlock}
      </Drawer>
    );
  }

  // Desktop: standard fixed Sider
  return (
    <Sider
      width={220}
      style={{ background: "#576A8F" }}
    >
      {logoBlock}
      {menuBlock}
    </Sider>
  );
}
