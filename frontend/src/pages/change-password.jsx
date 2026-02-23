import { Form, Input, Button, Card, message, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@auth/authContext";
import { changePassword as changePasswordApi } from "@api/authApi";

const { Title, Text } = Typography;

export default function ChangePassword() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values) => {
    try {
      const updatedUser = await changePasswordApi({
        password: values.password,
        passwordConfirm: values.confirmPassword,
      });

      // Update auth context with new user data (first_login = false)
      updateUser(updatedUser);

      message.success("Password updated successfully");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const errorMsg =
        err.response?.data?.password?.[0] ||
        err.response?.data?.password_confirm?.[0] ||
        err.response?.data?.detail ||
        "Failed to change password";
      message.error(errorMsg);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundImage:
          "url(https://images.unsplash.com/photo-1521791136064-7986c2920216)",
        backgroundSize: "cover",
        backgroundPosition: "center",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Card
        style={{
          width: "100%",
          maxWidth: 420,
          margin: "0 16px",
          padding: "16px 8px",
          borderRadius: 12,
          boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
        }}
      >
        <Title level={3} style={{ marginBottom: 4 }}>
          Change Password
        </Title>
        <Text type="secondary">
          {user?.firstLogin
            ? "This is your first login. Please set a new password."
            : "Enter a new password for your account."}
        </Text>

        <Form layout="vertical" onFinish={onFinish} style={{ marginTop: 24 }}>
          <Form.Item
            name="password"
            label="New Password"
            rules={[
              { required: true, message: "Please enter new password" },
              { min: 8, message: "Password must be at least 8 characters" },
            ]}
          >
            <Input.Password placeholder="Enter new password" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="Confirm Password"
            dependencies={["password"]}
            rules={[
              { required: true, message: "Please confirm password" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject("Passwords do not match");
                },
              }),
            ]}
          >
            <Input.Password placeholder="Re-enter new password" />
          </Form.Item>

          <Button
            htmlType="submit"
            block
            style={{
              background: "#1E232C",
              color: "#fff",
              height: 40,
              borderRadius: 6,
              marginTop: 8,
            }}
          >
            Update Password
          </Button>
        </Form>
      </Card>
    </div>
  );
}
