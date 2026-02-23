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
    <Layout style={{ minHeight: "100vh" }}>
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <Layout>
        <AppHeader
          isMobile={isMobile}
          onMenuClick={() => setMobileOpen(true)}
        />
        <Layout.Content style={{ padding: isMobile ? 12 : 24 }}>
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
