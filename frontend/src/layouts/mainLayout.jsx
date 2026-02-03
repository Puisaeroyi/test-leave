import { Layout } from "antd";
import { Outlet } from "react-router-dom";
import Sidebar from "@components/sidebar";
import AppHeader from "@components/header";

export default function MainLayout() {
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sidebar />
      <Layout>
        <AppHeader />
        <Layout.Content style={{ padding: 24 }}>
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
