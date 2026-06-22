import { useCallback, useEffect, useState } from "react";
import { Badge, Layout, Menu, Drawer, Grid } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@auth/authContext";
import { getPendingReviewCount } from "../api/dashboardApi";
import { PENDING_REVIEW_COUNT_CHANGED_EVENT } from "../lib/pending-review-notifications";
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
const REVIEW_COUNT_POLL_INTERVAL_MS = 60_000;

export default function Sidebar({ mobileOpen, onMobileClose }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();
  const [pendingReviewCount, setPendingReviewCount] = useState(0);

  // Compact navigation covers phones and portrait tablets (< 992px).
  const isMobile = !screens.lg;
  const canReview = user && (
    user.role === "MANAGER"
    || user.role === "HR"
    || user.role === "ADMIN"
    || user.isApprover
  );

  const refreshPendingReviewCount = useCallback(async () => {
    if (!canReview) {
      setPendingReviewCount(0);
      return;
    }

    try {
      setPendingReviewCount(await getPendingReviewCount());
    } catch (error) {
      console.error("Failed to fetch pending review count:", error);
    }
  }, [canReview]);

  useEffect(() => {
    if (!canReview) return undefined;

    refreshPendingReviewCount();
    window.addEventListener(
      PENDING_REVIEW_COUNT_CHANGED_EVENT,
      refreshPendingReviewCount,
    );
    const intervalId = window.setInterval(
      refreshPendingReviewCount,
      REVIEW_COUNT_POLL_INTERVAL_MS,
    );

    return () => {
      window.removeEventListener(
        PENDING_REVIEW_COUNT_CHANGED_EVENT,
        refreshPendingReviewCount,
      );
      window.clearInterval(intervalId);
    };
  }, [canReview, refreshPendingReviewCount]);

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

  if (canReview) {
    items.push({
      key: "/manager",
      icon: <TeamOutlined />,
      label: (
        <span className="sidebar-menu-label-with-badge">
          <span>Manager Reviews</span>
          <Badge count={pendingReviewCount} overflowCount={99} size="small" />
        </span>
      ),
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
        size="min(288px, calc(100vw - 32px))"
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
