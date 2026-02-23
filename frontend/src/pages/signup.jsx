import { Form, Input, Button, Card, message, Typography, Select, Row, Col } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { signup, getEntities, getLocations, getDepartments } from "@api/authApi";
import { useNavigate, Link } from "react-router-dom";
import { useEffect, useState } from "react";

const { Title, Text } = Typography;

export default function Signup() {
  const navigate = useNavigate();
  const [entities, setEntities] = useState([]);
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    getEntities().then(setEntities);
  }, []);

  const onEntityChange = async (entityId) => {
    setLocations([]);
    setDepartments([]);
    const data = await getLocations(entityId);
    setLocations(data);
  };

  const onLocationChange = async (locationId) => {
    setDepartments([]);
    const data = await getDepartments(locationId);
    setDepartments(data);
  };

  const onFinish = async (values) => {
    try {
      await signup(values);
      message.success("Register successful");
      navigate("/login");
    } catch (err) {
      message.error(err.message);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundImage:
          "url(https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?q=80&w=1172&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)",
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
          maxWidth: 480,
          margin: "0 16px",
          borderRadius: 12,
          boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
        }}
      >
        {/* BACK */}
        <ArrowLeftOutlined
          style={{ fontSize: 18, cursor: "pointer" }}
          onClick={() => navigate(-1)}
        />

        {/* TITLE */}
        <Title level={3} style={{ marginTop: 16 }}>
          Sign up
        </Title>
        <Text type="secondary">
          Fill out the form to register a new account
        </Text>

        <Form layout="vertical" onFinish={onFinish} style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name="firstName" label="First Name" rules={[{ required: true, message: "Please enter your first name" }]}>
                <Input placeholder="Your first name" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="lastName" label="Last Name" rules={[{ required: true, message: "Please enter your last name" }]}>
                <Input placeholder="Your last name" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="employeeCode"
            label="Employee Code (Optional)"
            rules={[
              {
                pattern: /^[A-Za-z0-9-_]*$/,
                message: "Only letters, numbers, - and _ are allowed",
              },
            ]}
          >
            <Input placeholder="e.g. EMP001" />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[{ required: true, message: "Please input your email" }]}
          >
            <Input placeholder="yourname@example.com" />
          </Form.Item>

          <Form.Item name="entity" label="Company" rules={[{ required: true }]}>
            <Select
              placeholder="Select company"
              onChange={onEntityChange}
              options={entities.map((e) => ({
                value: e.id,
                label: e.entity_name,
              }))}
            />
          </Form.Item>

          {locations.length > 0 && (
            <Form.Item
              name="location"
              label="Location"
              rules={[{ required: true }]}
            >
              <Select
                placeholder="Select location"
                onChange={onLocationChange}
                options={locations.map((l) => ({
                  value: l.id,
                  label: `${l.location_name}, ${l.city}`,
                }))}
              />
            </Form.Item>
          )}

          {departments.length > 0 && (
            <Form.Item
              name="department"
              label="Department"
              rules={[{ required: true }]}
            >
              <Select
                placeholder="Select department"
                options={departments.map((d) => ({
                  value: d.id,
                  label: d.department_name,
                }))}
              />
            </Form.Item>
          )}

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true }]}
          >
            <Input.Password placeholder="Enter your password" />
          </Form.Item>

          <Form.Item
            name="password_confirm"
            label="Confirm Password"
            dependencies={["password"]}
            rules={[
              { required: true },
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
            <Input.Password placeholder="Re-enter your password" />
          </Form.Item>

          <Button
            htmlType="submit"
            block
            style={{
              background: "#1E232C",
              color: "#fff",
              height: 40,
              marginTop: 8,
            }}
          >
            Register
          </Button>
        </Form>

        <div style={{ textAlign: "center", marginTop: 16 }}>
          <Text>
            Already have an account? <Link to="/login">Login</Link>
          </Text>
        </div>
      </Card>
    </div>
  );
}
