import { Empty, Modal, Spin, Tag, Typography } from "antd";
import dayjs from "dayjs";

const { Paragraph, Text } = Typography;

export default function AnnouncementModal({
  announcement,
  loading = false,
  open,
  onClose,
}) {
  return (
    <Modal
      title={null}
      open={open}
      onCancel={onClose}
      footer={null}
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
              {announcement.is_active === false && <Tag>Inactive</Tag>}
              <Text type="secondary" className="announcement-article__meta">
              Posted {dayjs(announcement.created_at).format("MMM D, YYYY HH:mm")}
              {announcement.created_by ? ` by ${announcement.created_by}` : ""}
              </Text>
              {(announcement.starts_at || announcement.expires_at) && (
                <Text type="secondary" className="announcement-article__meta">
                  Visible {announcement.starts_at ? dayjs(announcement.starts_at).format("MMM D, YYYY HH:mm") : "now"}
                  {" to "}
                  {announcement.expires_at ? dayjs(announcement.expires_at).format("MMM D, YYYY HH:mm") : "no end date"}
                </Text>
              )}
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
