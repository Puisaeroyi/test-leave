import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Select,
  Popconfirm,
  message,
  Typography,
  Tooltip,
  Input,
  Row,
  Col,
  Statistic,
} from "antd";
import {
  SettingOutlined,
  EditOutlined,
  SaveOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import { getAllUsers, updateUser, deleteUser } from "@api/userApi";
import "./Settings.css";

const { Title, Text } = Typography;

const Settings = () => {
  const { user } = useAuth();
  const [form] = Form.useForm();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [saving, setSaving] = useState(false);

  // Check if user has access (HR or Admin only)
  if (!user || (user.role !== "HR" && user.role !== "ADMIN")) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <Title level={3}>Access Denied</Title>
        <Text type="secondary">You don't have permission to access this page.</Text>
      </div>
    );
  }

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await getAllUsers();
      setUsers(data.results || data);
    } catch (error) {
      message.error("Failed to load users: " + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleEdit = (userData) => {
    setSelectedUser(userData);
    form.setFieldsValue({
      first_name: userData.first_name,
      last_name: userData.last_name,
      email: userData.email,
      employee_code: userData.employee_code,
      approver: userData.approver?.id || null,
    });
    setEditModalVisible(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      await updateUser(selectedUser.id, {
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        employee_code: values.employee_code || null,
        approver: values.approver || null,
      });

      message.success("User updated successfully");
      setEditModalVisible(false);
      fetchUsers();
    } catch (error) {
      message.error("Failed to update user: " + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (userId) => {
    try {
      await deleteUser(userId);
      message.success("User deleted successfully");
      fetchUsers();
    } catch (error) {
      message.error("Failed to delete user: " + (error.response?.data?.error || error.message));
    }
  };

  const columns = [
    {
      title: "Employee Code",
      dataIndex: "employee_code",
      key: "employee_code",
      width: 120,
    },
    {
      title: "Name",
      dataIndex: "first_name",
      key: "name",
      width: 160,
      render: (first_name, record) => `${first_name} ${record.last_name}`.trim() || record.email,
      sorter: (a, b) => `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`),
    },
    {
      title: "Email",
      dataIndex: "email",
      key: "email",
      width: 220,
    },
    {
      title: "Role",
      dataIndex: "role",
      key: "role",
      width: 100,
      render: (role) => {
        const colors = {
          ADMIN: "red",
          HR: "magenta",
          MANAGER: "gold",
          EMPLOYEE: "blue",
        };
        return <Tag color={colors[role]}>{role}</Tag>;
      },
      filters: [
        { text: "Admin", value: "ADMIN" },
        { text: "HR", value: "HR" },
        { text: "Manager", value: "MANAGER" },
        { text: "Employee", value: "EMPLOYEE" },
      ],
      onFilter: (value, record) => record.role === value,
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status) => (
        <Tag color={status === "ACTIVE" ? "green" : "default"}>{status}</Tag>
      ),
      filters: [
        { text: "Active", value: "ACTIVE" },
        { text: "Inactive", value: "INACTIVE" },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: "Entity",
      dataIndex: "entity",
      key: "entity",
      width: 120,
      render: (entity) => entity?.entity_name || "-",
    },
    {
      title: "Department",
      dataIndex: "department",
      key: "department",
      width: 140,
      render: (department) => department?.department_name || "-",
    },
    {
      title: "Approver",
      dataIndex: "approver",
      key: "approver",
      width: 150,
      render: (approver) => (
        approver ? (
          <Tooltip title={`${approver.first_name} ${approver.last_name} (${approver.email})`}>
            <Tag color="purple">{`${approver.first_name} ${approver.last_name}`.trim() || approver.email}</Tag>
          </Tooltip>
        ) : (
          <Tag color="default">Not assigned</Tag>
        )
      ),
    },
    {
      title: "Action",
      key: "action",
      width: 140,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Edit
          </Button>
          {/* Only Admin can delete users */}
          {user?.role === "ADMIN" && record.id !== user?.id && (
            <Popconfirm
              title="Delete User"
              description={`Are you sure you want to delete ${record.first_name} ${record.last_name || record.email}?`}
              onConfirm={() => handleDelete(record.id)}
              okText="Yes"
              cancelText="No"
              okButtonProps={{ danger: true }}
            >
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                size="small"
              >
                Delete
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  // Filter users for approver dropdown (exclude self and inactive users)
  const availableApprovers = users.filter(
    (u) => u.is_active && u.id !== selectedUser?.id
  );

  // Statistics
  const stats = {
    total: users.length,
    active: users.filter((u) => u.status === "ACTIVE").length,
    withoutApprover: users.filter(
      (u) => !u.approver && u.role === "EMPLOYEE"
    ).length,
  };

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Users"
              value={stats.total}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Active Users"
              value={stats.active}
              valueStyle={{ color: "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Employees Without Approver"
              value={stats.withoutApprover}
              valueStyle={{ color: stats.withoutApprover > 0 ? "#cf1322" : undefined }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <Space>
            <SettingOutlined />
            <span>User Management Settings</span>
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchUsers}
            loading={loading}
          >
            Refresh
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} users`,
          }}
        />
      </Card>

      <Modal
        title="Edit User"
        open={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
        confirmLoading={saving}
        okText="Save"
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            label="First Name"
            name="first_name"
            rules={[{ required: true, message: "Please enter first name" }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Last Name"
            name="last_name"
            rules={[{ required: true, message: "Please enter last name" }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Email"
            name="email"
            rules={[
              { required: true, message: "Please enter email" },
              { type: "email", message: "Please enter a valid email" },
            ]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Employee Code"
            name="employee_code"
          >
            <Input placeholder="Optional" />
          </Form.Item>

          <Form.Item
            label="Approver"
            name="approver"
            tooltip="Leave empty for HR/Admin/Manager roles"
          >
            <Select
              allowClear
              showSearch
              placeholder="Select an approver"
              filterOption={(input, option) =>
                (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              options={availableApprovers.map((u) => ({
                value: u.id,
                label: `${u.first_name} ${u.last_name}`.trim() || u.email,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;
