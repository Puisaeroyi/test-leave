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
import { login as loginApi, googleLogin } from "@api/authApi";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@auth/authContext";
import { useEffect, useState } from "react";

const { Title, Text } = Typography;

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [googleScriptLoaded, setGoogleScriptLoaded] = useState(false);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    try {
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
      message.error(err.message || "Login failed");
    }
  };

  // Load Google Identity Services script
  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      console.warn("VITE_GOOGLE_CLIENT_ID not set, Google Sign-In disabled");
      return;
    }

    // Load GSI script
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleScriptLoaded(true);
    script.onerror = () => console.error("Failed to load Google Identity Services");
    document.body.appendChild(script);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  // Handle Google credential response
  const handleGoogleCredentialResponse = async (response) => {
    setLoading(true);
    try {
      const user = await googleLogin(response.credential);
      login(user);
      message.success("Login successful");

      if (user.first_login) {
        navigate("/change-password", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      message.error(err.message || "Google login failed");
    } finally {
      setLoading(false);
    }
  };

  // Initialize Google Sign-In button
  useEffect(() => {
    if (!googleScriptLoaded || loading) return;

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) return;

    // Clean up existing button if any
    const existingButton = document.getElementById("google-signin-button");
    if (existingButton) {
      existingButton.innerHTML = "";
    }

    // Initialize Google Sign-In
    if (window.google && window.google.accounts) {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      // Render the button
      window.google.accounts.id.renderButton(
        document.getElementById("google-signin-button"),
        {
          theme: "outline",
          size: "large",
          type: "standard",
          shape: "rectangular",
          text: "signin_with",
          logo_alignment: "left",
          width: 400,
        }
      );
    }
  }, [googleScriptLoaded, loading]);

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
            <Input placeholder="Enter your company email" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: "Please input your password" }]}
          >
            <Input.Password placeholder="Enter your password" />
          </Form.Item>

          {/* REMEMBER */}
          <div style={{ marginBottom: 16 }}>
            <Checkbox>Remember password</Checkbox>
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
        <Divider plain style={{ margin: "24px 0" }}>OR</Divider>

        {/* GOOGLE SIGN-IN BUTTON */}
        <div
          id="google-signin-button"
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: 40,
          }}
        />

      </Card>
    </div>
  );
}
