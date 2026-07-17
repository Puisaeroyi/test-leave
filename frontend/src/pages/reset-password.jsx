import { useMemo, useState } from "react";
import { Form, Input, Button, Card, Typography, App } from "antd";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "@api/authApi";
import logo from "@/assets/logo.png";

const { Title, Text, Paragraph } = Typography;

export default function ResetPassword() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [linkInvalid, setLinkInvalid] = useState(false);

  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";
  const missingParams = useMemo(() => !uid || !token, [uid, token]);

  const onFinish = async (values) => {
    try {
      setLoading(true);
      await confirmPasswordReset({
        uid,
        token,
        password: values.password,
        passwordConfirm: values.confirmPassword,
      });
      message.success("Password reset successfully. You can sign in now.");
      navigate("/login", { replace: true });
    } catch (err) {
      const data = err.response?.data;
      const status = err.response?.status;
      const fieldError =
        data?.password?.[0] ||
        data?.password_confirm?.[0] ||
        data?.non_field_errors?.[0];
      if (fieldError) {
        message.error(fieldError);
        return;
      }
      // Only treat explicit invalid-link API responses as a dead link.
      // Network/5xx errors must not discard a still-valid token.
      if (status === 400 && data?.error) {
        setLinkInvalid(true);
        message.error(data.error);
        return;
      }
      message.error(
        data?.error ||
          data?.detail ||
          "Unable to reset password. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  if (missingParams || linkInvalid) {
    return (
      <main className="auth-shell">
        <section className="auth-hero">
          <div className="auth-kicker">Account Recovery</div>
          <h1 className="auth-title">Link unavailable.</h1>
          <p className="auth-copy">
            Password reset links expire after one hour and can only be used once.
          </p>
        </section>
        <Card className="auth-card login-card">
          <div className="login-card__brand">
            <img src={logo} alt="Company logo" className="login-card__logo" />
          </div>
          <Title level={3} className="auth-card-title">
            Invalid or expired link
          </Title>
          <Paragraph className="auth-card-subtitle">
            This reset link is invalid or has expired. Request a new one to continue.
          </Paragraph>
          <Form className="login-form" layout="vertical">
            <Link to="/forgot-password">
              <Button type="primary" className="app-button-primary login-form__submit" block>
                Request a new reset link
              </Button>
            </Link>
            <div style={{ marginTop: 16, textAlign: "center" }}>
              <Link to="/login">Back to login</Link>
            </div>
          </Form>
        </Card>
      </main>
    );
  }

  return (
    <main className="auth-shell">
      <section className="auth-hero">
        <div className="auth-kicker">Account Recovery</div>
        <h1 className="auth-title">Choose a new password.</h1>
        <p className="auth-copy">
          Enter a strong password you have not used elsewhere, then confirm it.
        </p>
      </section>

      <Card className="auth-card login-card">
        <div className="login-card__brand">
          <img src={logo} alt="Company logo" className="login-card__logo" />
        </div>
        <Title level={3} className="auth-card-title">
          Reset Password
        </Title>
        <Text className="auth-card-subtitle">Set a new password for your account.</Text>

        <Form layout="vertical" onFinish={onFinish} className="login-form">
          <Form.Item
            name="password"
            label="New Password"
            rules={[
              { required: true, message: "Please enter a new password" },
              { min: 8, message: "Password must be at least 8 characters" },
            ]}
          >
            <Input.Password placeholder="Enter new password" autoComplete="new-password" />
          </Form.Item>

          <Form.Item
            className="login-form__password"
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
                  return Promise.reject(new Error("Passwords do not match"));
                },
              }),
            ]}
          >
            <Input.Password placeholder="Re-enter new password" autoComplete="new-password" />
          </Form.Item>

          <Button
            type="primary"
            className="app-button-primary login-form__submit"
            htmlType="submit"
            block
            loading={loading}
          >
            Reset password
          </Button>
        </Form>

        <div style={{ marginTop: 16, textAlign: "center" }}>
          <Link to="/login">Back to login</Link>
        </div>
      </Card>
    </main>
  );
}
