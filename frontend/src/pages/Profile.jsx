import { useState, useEffect } from "react";
import { Card, Avatar, Typography, Descriptions, Tag, Button, message } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getCurrentUser } from "../api/authApi";

const { Title, Text } = Typography;

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const data = await getCurrentUser();
      setUser(data);
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      message.error("Failed to load profile");
      // Redirect to login if not authenticated
      if (error.response?.status === 401) {
        navigate("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Text>Loading...</Text>;
  }

  if (!user) {
    return <Text>You are not logged in</Text>;
  }

  const displayName = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;

  return (
    <div
      style={{
        maxWidth: 900,
        margin: "32px auto",
        padding: "0 16px",
      }}
    >
      <Card
        style={{
          borderRadius: 12,
          boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
        }}
      >
        {/* HEADER */}
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <Avatar size={96} src={user.avatar_url} icon={<UserOutlined />} />

          <div>
            <Title level={3} style={{ marginBottom: 4 }}>
              {displayName}
            </Title>
            <Text type="secondary">{user.email}</Text>
            <div style={{ marginTop: 8 }}>
              <Tag color={user.role === "MANAGER" ? "gold" : user.role === "ADMIN" ? "red" : "blue"}>
                {user.role}
              </Tag>
            </div>
          </div>
        </div>

        {/* INFO */}
        <Descriptions
          bordered
          column={2}
          style={{ marginTop: 32 }}
          labelStyle={{ fontWeight: 500 }}
        >
          <Descriptions.Item label="Employee Code">
            {user.employee_code || "-"}
          </Descriptions.Item>

          <Descriptions.Item label="Email">{user.email}</Descriptions.Item>

          <Descriptions.Item label="Location">
            {user.location_name || "-"}
          </Descriptions.Item>

          <Descriptions.Item label="Entity">
            {user.entity_name || "-"}
          </Descriptions.Item>

          <Descriptions.Item label="Department">
            {user.department_name || "-"}
          </Descriptions.Item>

          <Descriptions.Item label="Role">
            <Tag color={user.role === "MANAGER" ? "gold" : user.role === "ADMIN" ? "red" : "blue"}>
              {user.role}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="Join Date">
            {user.join_date || "-"}
          </Descriptions.Item>

          <Descriptions.Item label="Approver">
            {user.approver ? (
              <Tag color="purple">{user.approver.full_name}</Tag>
            ) : ["MANAGER", "ADMIN", "HR"].includes(user.role) ? (
              <Text type="secondary">N/A</Text>
            ) : (
              <Text type="secondary">Not assigned</Text>
            )}
          </Descriptions.Item>
        </Descriptions>

        {/* ACTION */}
        <div style={{ marginTop: 24, textAlign: "right" }}>
          <Button onClick={() => navigate(-1)}>Back</Button>
        </div>
      </Card>
    </div>
  );
}
