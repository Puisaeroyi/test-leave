import { useState, useEffect, useRef, useCallback } from "react";
import { Card, Avatar, Typography, Descriptions, Tag, Button, message } from "antd";
import { UserOutlined, CameraOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getCurrentUser, updateAvatar } from "../api/authApi";
import { useAuth } from "@auth/authContext";
import ProfileChangePasswordForm from "../components/profile-change-password-form";

const { Title, Text } = Typography;

// Format today's resolved shift for the Profile row.
const getTodayShiftLabel = (today, parentName) => {
  if (!today) return "-";
  if (!today.is_working) return "Off";

  const range = today.start_time && today.end_time
    ? `${today.start_time} - ${today.end_time}`
    : "";
  const sub = today.shift_name && today.shift_name !== parentName
    ? ` — ${today.shift_name}`
    : "";
  const base = `${parentName || today.shift_name || ""}${sub}`.trim();

  return range ? `${base} | ${range}` : base || "-";
};

export default function Profile() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const fileInputRef = useRef(null);

  const fetchUserProfile = useCallback(async () => {
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
  }, [navigate]);

  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

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
    return <Text style={{ color: "var(--color-muted)" }}>Loading...</Text>;
  }

  if (!user) {
    return <Text style={{ color: "var(--color-muted)" }}>You are not logged in</Text>;
  }

  const displayName = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;
  const roleTone = user.role === "MANAGER" ? "warning" : user.role === "ADMIN" ? "danger" : "accent";
  const roleTagStyle = {
    color: `var(--color-${roleTone})`,
    background: `var(--color-${roleTone}-soft)`,
    border: `1px solid var(--color-${roleTone})`,
  };
  const approverTagStyle = {
    color: "var(--color-info)",
    background: "var(--color-info-soft)",
    border: "1px solid var(--color-info)",
  };
  const finalApproverTagStyle = {
    color: "var(--color-warning)",
    background: "var(--color-warning-soft)",
    border: "1px solid var(--color-warning)",
  };

  return (
    <div className="page-shell">
      <section>
        <div className="page-kicker">My Workplace Profile</div>
        <h1 className="page-title">Profile</h1>
        <p className="page-subtitle">
          Review your organization details, approver, and avatar used across the leave planner.
        </p>
      </section>

      <Card className="page-panel">
        {/* HEADER */}
        <div className="profile-hero">
          <div className="profile-avatar-wrap">
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
              <button
                type="button"
                className="profile-avatar-action"
                onClick={handleAvatarClick}
                aria-label="Change profile avatar"
              >
                <CameraOutlined style={{ fontSize: 14 }} />
              </button>
            )}
            {avatarLoading && (
              <div className="profile-avatar-action">
                <div className="profile-spinner" />
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
            <Title level={3} style={{ marginBottom: 4, color: "var(--color-text)" }}>
              {displayName}
            </Title>
            <Text style={{ color: "var(--color-muted)" }}>{user.email}</Text>
            <div style={{ marginTop: 8 }}>
              <Tag style={roleTagStyle}>
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

          <Descriptions.Item label="Work Shift">
            {user.work_shift
              ? getTodayShiftLabel(user.work_shift_today, user.work_shift.name)
              : "-"}
          </Descriptions.Item>

          <Descriptions.Item label="Join Date">
            {user.join_date || "-"}
          </Descriptions.Item>

          <Descriptions.Item label="First Approver">
            {user.approver ? (
              <Tag style={approverTagStyle}>{user.approver.full_name}</Tag>
            ) : ["MANAGER", "ADMIN", "HR"].includes(user.role) ? (
              <Text type="secondary">N/A</Text>
            ) : (
              <Text type="secondary">Not assigned</Text>
            )}
          </Descriptions.Item>

          <Descriptions.Item label="Second Approver">
            {user.final_approver ? (
              <Tag style={finalApproverTagStyle}>{user.final_approver.full_name}</Tag>
            ) : ["MANAGER", "ADMIN", "HR"].includes(user.role) ? (
              <Text type="secondary">N/A</Text>
            ) : (
              <Text type="secondary">Not assigned</Text>
            )}
          </Descriptions.Item>
        </Descriptions>

        {/* ACTION — profile is primary; change password is a secondary modal action */}
        <div
          style={{
            marginTop: 24,
            display: "flex",
            justifyContent: "flex-end",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          <ProfileChangePasswordForm />
          <Button onClick={() => navigate(-1)}>Back</Button>
        </div>
      </Card>
    </div>
  );
}
