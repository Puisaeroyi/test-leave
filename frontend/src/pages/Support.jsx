import { Card, Typography, Space, Divider, Row, Col, Tag } from "antd";
import {
  CustomerServiceOutlined,
  MailOutlined,
  PhoneOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
} from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;

export default function Support() {
  return (
    <div
      style={{
        maxWidth: 900,
        margin: "32px auto",
        padding: "0 16px",
      }}
    >
      <Card
        title={
          <Space>
            <CustomerServiceOutlined style={{ fontSize: 24 }} />
            <Title level={3} style={{ margin: 0 }}>
              Support Center
            </Title>
          </Space>
        }
        style={{
          borderRadius: 12,
          boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
        }}
      >
        {/* Help Message */}
        <Paragraph
          style={{
            fontSize: 16,
            marginBottom: 24,
            color: "#555",
          }}
        >
          For technical assistance or to report a bug, please reach out to our
          support team at:
        </Paragraph>

        <Divider />

        {/* Support Contact Card */}
        <Card
          type="inner"
          title="Contact Information"
          style={{
            marginBottom: 24,
            borderRadius: 8,
            background: "rgb(87, 106, 143)",
          }}
          headStyle={{
            color: "#fff",
            borderBottom: "1px solid rgba(255,255,255,0.2)",
            fontSize: 24,
            fontWeight: 600,
            paddingTop: 16,
            paddingBottom: 12,
          }}
          bodyStyle={{ background: "rgba(255,255,255,0.95)" }}
        >
          <Row gutter={[24, 24]}>
            {/* Name */}
            <Col xs={24} md={12}>
              <Space direction="vertical" size={6}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  Support Contact
                </Text>
                <Title level={3} style={{ margin: 0, fontSize: 22 }}>
                  Silver Bui
                </Title>
              </Space>
            </Col>

            {/* Email */}
            <Col xs={24} md={12}>
              <Space direction="vertical" size={6}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  Email
                </Text>
                <Space>
                  <MailOutlined style={{ color: "#1677ff", fontSize: 16 }} />
                  <a
                    href="mailto:silver@teampl.com"
                    style={{ fontSize: 18, fontWeight: 500 }}
                  >
                    silver@teampl.com
                  </a>
                </Space>
              </Space>
            </Col>

            {/* Phone */}
            <Col xs={24} md={12}>
              <Space direction="vertical" size={6}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  Phone (Kakao Talk)
                </Text>
                <Space>
                  <PhoneOutlined style={{ color: "#52c41a", fontSize: 16 }} />
                  <a
                    href="tel:+84902713536"
                    style={{ fontSize: 18, fontWeight: 500 }}
                  >
                    (+84) 902 713 536
                  </a>
                </Space>
              </Space>
            </Col>

            {/* Response Time */}
            <Col xs={24} md={12}>
              <Space direction="vertical" size={6}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  Response Time
                </Text>
                <Space>
                  <ClockCircleOutlined style={{ color: "#faad14", fontSize: 16 }} />
                  <Text style={{ fontSize: 18 }}>Within 24 hours</Text>
                </Space>
              </Space>
            </Col>
          </Row>
        </Card>
      </Card>
    </div>
  );
}
