import { Layout, Menu, Drawer, Grid } from "antd";
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

export default function Sidebar({ mobileOpen, onMobileClose }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();

  // Compact navigation covers phones and portrait tablets (< 992px).
  const isMobile = !screens.lg;

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
      label: "Manager Reviews",
    });
    items.push({
      key: "/business-trip-tickets",
      icon: <SendOutlined />,
      label: "Trip Reviews",
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
      className="sidebar-brand"
      onClick={() => {
        navigate("/dashboard");
        if (isMobile) onMobileClose?.();
      }}
    >
      <div className="sidebar-brand__mark">
        <img src={logo} alt="Leave Management" />
      </div>
    </div>
  );

  const menuBlock = (
    <Menu
      className="app-sidebar-menu"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={items}
      onClick={handleMenuClick}
    />
  );

  // Mobile: render as Drawer overlay
  if (isMobile) {
    return (
      <Drawer
        className="app-navigation-drawer"
        placement="left"
        open={mobileOpen}
        onClose={onMobileClose}
        width="min(288px, calc(100vw - 32px))"
        styles={{ body: { padding: 0 } }}
      >
        <div className="app-sidebar">
          {logoBlock}
          {menuBlock}
        </div>
      </Drawer>
    );
  }

  // Desktop: standard fixed Sider
  return (
    <Sider
      width={248}
      className="app-sidebar"
    >
      {logoBlock}
      {menuBlock}
    </Sider>
  );
}
