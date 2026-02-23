import { useState, useEffect, useRef } from "react";
import { Card, Avatar, Typography, Descriptions, Tag, Button, message } from "antd";
import { UserOutlined, CameraOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getCurrentUser, updateAvatar } from "../api/authApi";
import { useAuth } from "@auth/authContext";

const { Title, Text } = Typography;

export default function Profile() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const fileInputRef = useRef(null);

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

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      message.error('Invalid file type. Please upload JPG, PNG, GIF, or WebP.');
      return;
    }

    // Validate file size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      message.error('File size exceeds 2MB limit.');
      return;
    }

    try {
      setAvatarLoading(true);
      const updatedUser = await updateAvatar(file);
      setUser(updatedUser);
      updateUser(updatedUser); // Update auth context for header
      message.success('Avatar updated successfully!');
    } catch (error) {
      console.error("Failed to update avatar:", error);
      message.error(error.response?.data?.error || 'Failed to update avatar');
    } finally {
      setAvatarLoading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
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
    <>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
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
        <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>
          <div style={{ position: "relative", display: "inline-block" }}>
            <Avatar
              size={96}
              src={user.avatar_url}
              icon={<UserOutlined />}
              style={{
                cursor: avatarLoading ? "default" : "pointer",
                opacity: avatarLoading ? 0.6 : 1,
              }}
              onClick={avatarLoading ? undefined : handleAvatarClick}
            />
            {!avatarLoading && (
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  right: 0,
                  background: "#1890ff",
                  borderRadius: "50%",
                  width: 28,
                  height: 28,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  border: "2px solid #fff",
                }}
                onClick={handleAvatarClick}
              >
                <CameraOutlined style={{ color: "#fff", fontSize: 14 }} />
              </div>
            )}
            {avatarLoading && (
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  right: 0,
                  background: "rgba(0,0,0,0.6)",
                  borderRadius: "50%",
                  width: 28,
                  height: 28,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <div
                  style={{
                    width: 12,
                    height: 12,
                    border: "2px solid #fff",
                    borderTopColor: "transparent",
                    borderRadius: "50%",
                    animation: "spin 1s linear infinite",
                  }}
                />
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />

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
          column={{ xs: 1, sm: 1, md: 2 }}
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
    </>
  );
}
