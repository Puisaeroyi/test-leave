import {
  Form,
  Input,
  Button,
  Card,
  message,
  Typography,
  Checkbox,
  Divider,
} from "antd";
import { login as loginApi } from "@api/authApi";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@auth/authContext";

const { Title, Text } = Typography;

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values) => {
    try {
      const user = await loginApi(values);
      login(user);
      message.success("Login successful");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      message.error(err.message || "Login failed");
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
          width: 420,
          padding: "16px 8px",
          borderRadius: 12,
          boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
        }}
      >
        {/* SIGN UP LINK */}
        <div style={{ textAlign: "right", marginBottom: 12 }}>
          <Text>
            Don’t have an account?{" "}
            <Link to="/signup" style={{ fontWeight: 600 }}>
              Sign up now
            </Link>
          </Text>
        </div>

        {/* TITLE */}
        <Title level={3} style={{ marginBottom: 0 }}>
          Hello 👋
        </Title>
        <Text type="secondary">Login to continue</Text>

        {/* FORM */}
        <Form
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="email"
            label="Email"
            rules={[{ required: true, message: "Please input your email" }]}
          >
            <Input placeholder="yourname@teampl.com" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: "Please input your password" }]}
          >
            <Input.Password placeholder="Enter your password" />
          </Form.Item>

          {/* REMEMBER + FORGOT */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 16,
            }}
          >
            <Checkbox>Remember password</Checkbox>
            <Link to="/forgot-password">Forgot password?</Link>
          </div>

          {/* LOGIN BUTTON */}
          <Button
            htmlType="submit"
            block
            style={{
              background: "#1E232C",
              color: "#fff",
              height: 40,
              borderRadius: 6,
            }}
          >
            Login
          </Button>
        </Form>

        {/* DIVIDER */}
        <Divider plain style={{ margin: "24px 0" }}>
          Login with
        </Divider>

        {/* GOOGLE LOGIN */}
        <div style={{ textAlign: "center" }}>
          <img
            src="https://developers.google.com/identity/images/g-logo.png"
            alt="Google Login"
            style={{
              width: 36,
              cursor: "pointer",
            }}
          />
        </div>
      </Card>
    </div>
  );
}
