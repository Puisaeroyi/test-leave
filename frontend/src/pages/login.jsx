import {
  Form,
  Input,
  Button,
  Card,
  App,
  Typography,
} from "antd";
import { login as loginApi } from "@api/authApi";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@auth/authContext";
import { useState } from "react";
import logo from "@/assets/logo.png";

const { Title, Text } = Typography;

export default function Login() {
  const { message } = App.useApp();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    try {
      setLoading(true);
      const user = await loginApi(values);
      login(user);
      message.success("Login successful");

      // Redirect to change password if first login
      if (user.first_login) {
        navigate("/change-password", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      const errorData = err.response?.data;
      const errorMessage =
        errorData?.non_field_errors?.[0] ||
        errorData?.detail ||
        errorData?.error ||
        err.message ||
        "Login failed";
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };


  return (
    <main className="auth-shell">
      <section className="auth-hero">
        <div className="auth-kicker">Warm Office Leave</div>
        <h1 className="auth-title">Plan time off with calm clarity.</h1>
        <p className="auth-copy">
          A friendly workspace for leave balances, approvals, business trips, and team availability.
        </p>
      </section>

      <Card className="auth-card login-card">
          <div className="login-card__brand">
            <img src={logo} alt="Company logo" className="login-card__logo" />
          </div>
          <Title level={3} className="auth-card-title">
            Welcome Back
          </Title>
          <Text className="auth-card-subtitle">Sign in to continue</Text>

          <Form
            layout="vertical"
            onFinish={onFinish}
            className="login-form"
          >
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, message: "Please input your email" }]}
            >
              <Input placeholder="Enter your company email" />
            </Form.Item>

            <Form.Item
              className="login-form__password"
              name="password"
              label="Password"
              rules={[{ required: true, message: "Please input your password" }]}
            >
              <Input.Password placeholder="Enter your password" />
            </Form.Item>

            <Button
              type="primary"
              className="app-button-primary login-form__submit"
              htmlType="submit"
              block
              loading={loading}
            >
              Login
            </Button>
          </Form>
      </Card>
    </main>
  );
}
