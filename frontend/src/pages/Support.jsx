import { Card, Typography, Space } from "antd";
import {
  CustomerServiceOutlined,
  MailOutlined,
  PhoneOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";

const { Title, Paragraph } = Typography;

export default function Support() {
  return (
    <div className="page-shell">
      <section>
        <div className="page-kicker">Help & Support</div>
        <h1 className="page-title">Support Center</h1>
        <p className="page-subtitle">
          Need help or found an issue? Contact support and we will guide you through the next step.
        </p>
      </section>

      <Card
        className="page-panel"
        title={
          <Space>
            <CustomerServiceOutlined style={{ fontSize: 24 }} />
            <Title level={3} style={{ margin: 0, color: "var(--color-text)" }}>
              Contact Desk
            </Title>
          </Space>
        }
      >
        {/* Help Message */}
        <Paragraph style={{ color: "var(--color-muted)", fontSize: 16 }}>
          For technical assistance or to report a bug, please reach out to our
          support team at:
        </Paragraph>

        {/* Support Contact Card */}
        <div className="contact-grid">
            {/* Name */}
            <div className="contact-tile">
              <div className="contact-tile__label">Support Contact</div>
              <div className="contact-tile__value">Silver Bui</div>
            </div>

            {/* Email */}
            <div className="contact-tile">
              <div className="contact-tile__label">Email</div>
              <div className="contact-tile__value">
                <Space>
                  <MailOutlined style={{ color: "var(--color-accent)" }} />
                  <a
                    href="mailto:silver@teampl.com"
                  >
                    silver@teampl.com
                  </a>
                </Space>
              </div>
            </div>

            {/* Phone */}
            <div className="contact-tile">
              <div className="contact-tile__label">Phone (Kakao Talk)</div>
              <div className="contact-tile__value">
                <Space>
                  <PhoneOutlined style={{ color: "var(--color-success)" }} />
                  <a
                    href="tel:+84902713536"
                  >
                    (+84) 902 713 536
                  </a>
                </Space>
              </div>
            </div>

            {/* Response Time */}
            <div className="contact-tile">
              <div className="contact-tile__label">Response Time</div>
              <div className="contact-tile__value">
                <Space>
                  <ClockCircleOutlined style={{ color: "var(--color-warning)" }} />
                  <span>Within 24 hours</span>
                </Space>
              </div>
            </div>
        </div>
      </Card>
    </div>
  );
}
