import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  message,
} from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import {
  createAnnouncement,
  deleteAnnouncement,
  getAnnouncements,
  updateAnnouncement,
} from "@api/announcement-api";
import RichTextEditor from "@components/RichTextEditor";

const htmlToPlainText = (html) => {
  const element = document.createElement("div");
  element.innerHTML = html || "";
  return (element.textContent || element.innerText || "").trim();
};

const renderAnnouncementText = (value, fallback = "-") => {
  const text = value || fallback;
  return (
    <span className="announcement-table-text" title={text}>
      {text}
    </span>
  );
};

const getAnnouncementStatus = (announcement) => {
  if (announcement.is_expired) return { label: "Expired", color: "red" };
  if (announcement.is_scheduled) return { label: "Scheduled", color: "blue" };
  if (!announcement.is_active) return { label: "Inactive", color: "default" };
  return { label: "Active", color: "green" };
};

export default function AnnouncementManagement() {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState(null);
  const [form] = Form.useForm();

  const fetchAnnouncements = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAnnouncements({ include_inactive: true });
      setAnnouncements(data.results || []);
    } catch (error) {
      message.error("Failed to load announcements: " + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnnouncements();
  }, [fetchAnnouncements]);

  const openCreateModal = () => {
    setEditingAnnouncement(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true, active_range: null });
    setModalOpen(true);
  };

  const openEditModal = (announcement) => {
    setEditingAnnouncement(announcement);
    form.setFieldsValue({
      title: announcement.title,
      body: announcement.body,
      body_html: announcement.body_html || announcement.body,
      active_range: announcement.starts_at || announcement.expires_at
        ? [announcement.starts_at ? dayjs(announcement.starts_at) : null, announcement.expires_at ? dayjs(announcement.expires_at) : null]
        : null,
      is_active: announcement.is_active,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const plainBody = htmlToPlainText(values.body_html) || values.body;
      const payload = {
        ...values,
        body: plainBody,
        starts_at: values.active_range?.[0]?.toISOString() || null,
        expires_at: values.active_range?.[1]?.toISOString() || null,
      };
      delete payload.active_range;
      setSaving(true);
      if (editingAnnouncement) {
        await updateAnnouncement(editingAnnouncement.id, payload);
        message.success("Announcement updated");
      } else {
        await createAnnouncement(payload);
        message.success("Announcement created");
      }
      setModalOpen(false);
      await fetchAnnouncements();
    } catch (error) {
      if (error.errorFields) return;
      const errorData = error.response?.data;
      message.error(
        "Failed to save announcement: " +
          (errorData?.error || errorData?.title?.[0] || errorData?.body?.[0] || error.message)
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteAnnouncement(id);
      message.success("Announcement deleted");
      await fetchAnnouncements();
    } catch (error) {
      message.error("Failed to delete announcement: " + (error.response?.data?.error || error.message));
    }
  };

  const columns = [
    {
      title: "Title",
      dataIndex: "title",
      key: "title",
      width: 260,
      render: (value) => renderAnnouncementText(value),
    },
    {
      title: "Status",
      dataIndex: "is_active",
      key: "is_active",
      width: 100,
      render: (_, record) => {
        const status = getAnnouncementStatus(record);
        return <Tag color={status.color}>{status.label}</Tag>;
      },
    },
    {
      title: "Visible Window",
      key: "active_range",
      width: 230,
      render: (_, record) => {
        if (!record.starts_at && !record.expires_at) return "Always";
        const start = record.starts_at ? dayjs(record.starts_at).format("YYYY-MM-DD HH:mm") : "Now";
        const end = record.expires_at ? dayjs(record.expires_at).format("YYYY-MM-DD HH:mm") : "No end";
        return renderAnnouncementText(`${start} to ${end}`);
      },
    },
    {
      title: "Created By",
      key: "created_by",
      width: 160,
      render: (_, record) => renderAnnouncementText(record.created_by_name || record.created_by || "-"),
    },
    {
      title: "Action",
      key: "action",
      width: 76,
      align: "center",
      render: (_, record) => (
        <Space className="announcement-action-cell" size={6}>
          <Tooltip title="Edit announcement">
            <Button
              aria-label="Edit announcement"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEditModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete announcement"
            description="Are you sure you want to delete this announcement?"
            onConfirm={() => handleDelete(record.id)}
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Delete announcement">
              <Button
                aria-label="Delete announcement"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      className="page-panel table-card announcement-management-card"
      title="Announcement Articles"
      extra={
        <Space className="announcement-management-toolbar" wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            Add Announcement
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchAnnouncements} loading={loading}>
            Refresh
          </Button>
        </Space>
      }
    >
      <Table
        className="announcement-management-table"
        columns={columns}
        dataSource={announcements}
        rowKey="id"
        loading={loading}
        scroll={{ x: 950 }}
        pagination={{ responsive: true, size: "small" }}
        tableLayout="fixed"
        expandable={{
          expandedRowRender: (record) => record.body_html ? (
            <div className="rich-content" dangerouslySetInnerHTML={{ __html: record.body_html }} />
          ) : (
            <div style={{ whiteSpace: "pre-wrap" }}>{record.body}</div>
          ),
        }}
      />

      <Modal
        title={editingAnnouncement ? "Edit Announcement" : "Add Announcement"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        confirmLoading={saving}
        okText={editingAnnouncement ? "Save" : "Create"}
        width={680}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label="Title"
            name="title"
            rules={[{ required: true, message: "Please enter a title" }]}
          >
            <Input maxLength={200} placeholder="Announcement title" />
          </Form.Item>
          <Form.Item name="body" hidden>
            <Input />
          </Form.Item>
          <Form.Item
            label="Body"
            name="body_html"
            rules={[{ required: true, message: "Please enter announcement content" }]}
          >
            <RichTextEditor placeholder="Paste from Word, type formatted content, or insert images..." />
          </Form.Item>
          <Form.Item
            label="Visible From / To"
            name="active_range"
            tooltip="Leave empty to show the announcement while Active is on. When the end time passes, it becomes inactive automatically."
          >
            <DatePicker.RangePicker
              showTime
              allowEmpty={[true, true]}
              style={{ width: "100%" }}
              format="YYYY-MM-DD HH:mm"
            />
          </Form.Item>
          <Form.Item label="Active" name="is_active" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
