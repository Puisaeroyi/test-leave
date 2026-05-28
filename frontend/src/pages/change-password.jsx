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
    <main className="auth-shell">
      <section className="auth-hero">
        <div className="auth-kicker">Account Safety</div>
        <h1 className="auth-title">Set a password you can trust.</h1>
        <p className="auth-copy">
          Before you continue, choose a fresh password to keep your leave and profile data safe.
        </p>
      </section>

      <Card className="auth-card">
        <Title level={3} className="auth-card-title">
          Change Password
        </Title>
        <Text className="auth-card-subtitle">
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
            type="primary"
            className="app-button-primary"
            htmlType="submit"
            block
          >
            Update Password
          </Button>
        </Form>
      </Card>
    </main>
  );
}
