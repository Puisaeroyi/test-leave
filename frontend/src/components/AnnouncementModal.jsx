import { Button, Empty, Modal, Spin, Tag, Typography } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

const { Paragraph, Text } = Typography;

export default function AnnouncementModal({
  announcement,
  loading = false,
  open,
  onClose,
  index = 0,
  total = 1,
  onPrev,
  onNext,
}) {
  const createdBy = announcement?.created_by_name || announcement?.created_by;

  // Show Prev/Next stepper only when cycling multiple announcements (login pop-up).
  const stepperFooter =
    total > 1 ? (
      <div className="announcement-stepper">
        <Button
          icon={<LeftOutlined />}
          onClick={onPrev}
          disabled={index <= 0}
        >
          Prev
        </Button>
        <Text type="secondary">{`${index + 1} of ${total}`}</Text>
        <Button
          onClick={onNext}
          disabled={index >= total - 1}
        >
          Next <RightOutlined />
        </Button>
      </div>
    ) : null;

  return (
    <Modal
      title={null}
      open={open}
      onCancel={onClose}
      footer={stepperFooter}
      width={860}
      className="announcement-article-modal"
    >
      <Spin spinning={loading}>
        {!announcement ? (
          <Empty description="No announcements" />
        ) : (
          <article className="announcement-article">
            <header className="announcement-article__header">
              <div className="announcement-article__kicker">Company Announcement</div>
              <Typography.Title level={1} className="announcement-article__title">
                {announcement.title}
              </Typography.Title>
              <div className="announcement-article__meta-stack">
                {announcement.is_active === false && <Tag>Inactive</Tag>}
                <Text type="secondary" className="announcement-article__meta">
                  Posted {dayjs(announcement.created_at).format("MMM D, YYYY HH:mm")}
                  {createdBy ? ` by ${createdBy}` : ""}
                </Text>
                {(announcement.starts_at || announcement.expires_at) && (
                  <Text type="secondary" className="announcement-article__meta">
                    Visible {announcement.starts_at ? dayjs(announcement.starts_at).format("MMM D, YYYY HH:mm") : "now"}
                    {" to "}
                    {announcement.expires_at ? dayjs(announcement.expires_at).format("MMM D, YYYY HH:mm") : "no end date"}
                  </Text>
                )}
              </div>
            </header>
            {announcement.body_html ? (
              <div
                className="rich-content announcement-detail-content"
                dangerouslySetInnerHTML={{ __html: announcement.body_html }}
              />
            ) : (
              <Paragraph style={{ marginTop: 12, whiteSpace: "pre-wrap" }}>
                {announcement.body}
              </Paragraph>
            )}
          </article>
        )}
      </Spin>
    </Modal>
  );
}
