import { useState } from "react";
import { Form, Input, Button, Card, Typography, App } from "antd";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "@api/authApi";
import logo from "@/assets/logo.png";

const { Title, Text, Paragraph } = Typography;

export default function ForgotPassword() {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const onFinish = async (values) => {
    try {
      setLoading(true);
      await requestPasswordReset(values.email);
      setSubmitted(true);
    } catch (err) {
      const errorMsg =
        err.response?.data?.email?.[0] ||
        err.response?.data?.detail ||
        err.response?.data?.error ||
        "Unable to send reset email. Please try again.";
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-hero">
        <div className="auth-kicker">Account Recovery</div>
        <h1 className="auth-title">Reset your password.</h1>
        <p className="auth-copy">
          Enter the email on your account and we will send a secure reset link if it matches.
        </p>
      </section>

      <Card className="auth-card login-card">
        <div className="login-card__brand">
          <img src={logo} alt="Company logo" className="login-card__logo" />
        </div>
        <Title level={3} className="auth-card-title">
          Forgot Password
        </Title>

        {submitted ? (
          <>
            <Paragraph className="auth-card-subtitle">
              Check your email — if an account exists, a reset link was sent. The link expires in 1
              hour.
            </Paragraph>
            <Form className="login-form" layout="vertical">
              <Link to="/login">
                <Button type="primary" className="app-button-primary login-form__submit" block>
                  Back to login
                </Button>
              </Link>
            </Form>
          </>
        ) : (
          <>
            <Text className="auth-card-subtitle">
              We will email you a one-time link to set a new password.
            </Text>
            <Form layout="vertical" onFinish={onFinish} className="login-form">
              <Form.Item
                name="email"
                label="Email"
                rules={[
                  { required: true, message: "Please enter your email" },
                  { type: "email", message: "Enter a valid email address" },
                ]}
              >
                <Input placeholder="Enter your company email" autoComplete="email" />
              </Form.Item>

              <Button
                type="primary"
                className="app-button-primary login-form__submit"
                htmlType="submit"
                block
                loading={loading}
              >
                Send reset link
              </Button>
            </Form>
            <div style={{ marginTop: 16, textAlign: "center" }}>
              <Link to="/login">Back to login</Link>
            </div>
          </>
        )}
      </Card>
    </main>
  );
}
