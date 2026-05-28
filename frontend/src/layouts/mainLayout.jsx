import { useState } from "react";
import { Layout, Grid } from "antd";
import { Outlet } from "react-router-dom";
import Sidebar from "@components/sidebar";
import AppHeader from "@components/header";

const { useBreakpoint } = Grid;

export default function MainLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  return (
    <Layout className="app-shell">
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <Layout style={{ background: "transparent" }}>
        <AppHeader
          isMobile={isMobile}
          onMenuClick={() => setMobileOpen(true)}
        />
        <Layout.Content className="app-content">
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
