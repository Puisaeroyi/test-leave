import { useState, useEffect, useCallback } from "react";
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
  DatePicker,
  Tabs,
} from "antd";
import dayjs from "dayjs";
import {
  SettingOutlined,
  EditOutlined,
  ReloadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import { getAllUsers, updateUser, deleteUser, createUser } from "@api/userApi";
import { getEntities, getLocations, getDepartments } from "@api/authApi";
import { exportApprovedLeaves } from "@api/dashboardApi";
import AnnouncementManagement from "@components/AnnouncementManagement";
import EntityManagement from "@components/EntityManagement";
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
  const [exportRange, setExportRange] = useState([
    dayjs().startOf("month"),
    dayjs().add(1, "month").startOf("month"),
  ]);
  const [exporting, setExporting] = useState(false);

  // Add User modal state
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [addForm] = Form.useForm();
  const [entities, setEntities] = useState([]);
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [creating, setCreating] = useState(false);
  const hasSettingsAccess = user?.role === "HR" || user?.role === "ADMIN";

  const fetchUsers = useCallback(async () => {
    if (!hasSettingsAccess) return;

    setLoading(true);
    try {
      const data = await getAllUsers();
      setUsers(data.results || data);
    } catch (error) {
      message.error("Failed to load users: " + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  }, [hasSettingsAccess]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Check if user has access (HR or Admin only)
  if (!hasSettingsAccess) {
    return (
      <div className="page-shell" style={{ textAlign: "center" }}>
        <Title level={3}>Access Denied</Title>
        <Text type="secondary">You don't have permission to access this page.</Text>
      </div>
    );
  }

  const handleEdit = (userData) => {
    setSelectedUser(userData);
    form.setFieldsValue({
      first_name: userData.first_name,
      last_name: userData.last_name,
      email: userData.email,
      employee_code: userData.employee_code,
      approver: userData.approver?.id || null,
      final_approver: userData.final_approver?.id || null,
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
        final_approver: values.final_approver || null,
      });

      message.success("User updated successfully");
      setEditModalVisible(false);
      await fetchUsers();
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
      await fetchUsers();
    } catch (error) {
      message.error("Failed to delete user: " + (error.response?.data?.error || error.message));
    }
  };

  const handleExport = async () => {
    if (!exportRange || exportRange.length !== 2) {
      message.warning("Please select a date range");
      return;
    }
    setExporting(true);
    try {
      const startDate = exportRange[0].format("YYYY-MM-DD");
      const endDate = exportRange[1].format("YYYY-MM-DD");
      const blob = await exportApprovedLeaves(startDate, endDate);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `approved_leaves_${startDate}_to_${endDate}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
      message.success("Export downloaded");
    } catch (error) {
      message.error("Export failed: " + (error.response?.data?.error || error.message));
    } finally {
      setExporting(false);
    }
  };

  // Add User handlers
  const handleAddUser = async () => {
    addForm.resetFields();
    setLocations([]);
    setDepartments([]);
    setAddModalVisible(true);
    try {
      const data = await getEntities();
      setEntities(data.results || data);
    } catch {
      message.error("Failed to load entities");
    }
  };

  const handleEntityChange = async (entityId) => {
    addForm.setFieldsValue({ location: undefined, department: undefined });
    setDepartments([]);
    if (!entityId) { setLocations([]); return; }
    try {
      const data = await getLocations(entityId);
      setLocations(data.results || data);
    } catch {
      message.error("Failed to load locations");
    }
  };

  const handleLocationChange = async (locationId) => {
    addForm.setFieldsValue({ department: undefined });
    if (!locationId) { setDepartments([]); return; }
    try {
      const data = await getDepartments(locationId);
      setDepartments(data.results || data);
    } catch {
      message.error("Failed to load departments");
    }
  };

  const handleCreateUser = async () => {
    try {
      const values = await addForm.validateFields();
      setCreating(true);
      await createUser({
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name,
        employee_code: values.employee_code || null,
        role: values.role,
        entity: values.entity,
        location: values.location,
        department: values.department,
        approver: values.approver,
        final_approver: values.final_approver || null,
        join_date: values.join_date?.format("YYYY-MM-DD") || null,
      });
      message.success("User created successfully");
      setAddModalVisible(false);
      addForm.resetFields();
      await fetchUsers();
    } catch (error) {
      if (error.errorFields) return; // Form validation errors
      const errData = error.response?.data;
      const errMsg = errData?.error || errData?.email?.[0] || error.message;
      message.error("Failed to create user: " + errMsg);
    } finally {
      setCreating(false);
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
        const roleTagStyles = {
          ADMIN: { color: "var(--color-danger)", background: "var(--color-danger-soft)", border: "1px solid var(--color-danger)" },
          HR: { color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" },
          MANAGER: { color: "var(--color-warning)", background: "var(--color-warning-soft)", border: "1px solid var(--color-warning)" },
          EMPLOYEE: { color: "var(--color-accent)", background: "var(--color-accent-soft)", border: "1px solid var(--color-accent)" },
        };
        return <Tag style={roleTagStyles[role]}>{role}</Tag>;
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
        <Tag
          style={status === "ACTIVE"
            ? { color: "var(--color-success)", background: "var(--color-success-soft)", border: "1px solid var(--color-success)" }
            : { color: "var(--color-muted)", background: "var(--color-surface-muted)", border: "1px solid var(--color-border)" }}
        >
          {status}
        </Tag>
      ),
    },
    {
      title: "Entity",
      dataIndex: "entity",
      key: "entity",
      width: 150,
      render: (entity) => entity?.entity_name || "-",
      filters: Array.from(new Set(users.map(u => u.entity?.entity_name).filter(Boolean)))
        .sort()
        .map(name => ({ text: name, value: name })),
      onFilter: (value, record) => record.entity?.entity_name === value,
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
            <Tag className="approver-tag" style={{ color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }}>{`${approver.first_name} ${approver.last_name}`.trim() || approver.email}</Tag>
          </Tooltip>
        ) : (
          <Tag style={{ color: "var(--color-muted)", background: "var(--color-surface-muted)", border: "1px solid var(--color-border)" }}>Not assigned</Tag>
        )
      ),
    },
    {
      title: "Final Approver",
      dataIndex: "final_approver",
      key: "final_approver",
      width: 160,
      render: (approver) => (
        approver ? (
          <Tooltip title={`${approver.first_name} ${approver.last_name} (${approver.email})`}>
            <Tag style={{ color: "var(--color-success)", background: "var(--color-success-soft)", border: "1px solid var(--color-success)" }}>
              {`${approver.first_name} ${approver.last_name}`.trim() || approver.email}
            </Tag>
          </Tooltip>
        ) : (
          <Tag style={{ color: "var(--color-muted)", background: "var(--color-surface-muted)", border: "1px solid var(--color-border)" }}>Not assigned</Tag>
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
    (u) => u.status === "ACTIVE" && u.id !== selectedUser?.id
  );

  // Statistics
  const stats = {
    total: users.length,
    active: users.filter((u) => u.status === "ACTIVE").length,
    withoutApprover: users.filter(
      (u) => !u.approver && (u.role === "EMPLOYEE" || u.role === "MANAGER")
    ).length,
  };

  // Tab items configuration
  const tabItems = [
    {
      key: 'users',
      label: 'Users',
      children: (
        <div>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={8}>
              <Card className="page-panel">
                <Statistic
                  title="Total Users"
                  value={stats.total}
                  prefix={<SettingOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card className="page-panel">
                <Statistic
                  title="Active Users"
                  value={stats.active}
                  valueStyle={{ color: "var(--color-success)" }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card className="page-panel">
                <Statistic
                  title="Users Without Approver"
                  value={stats.withoutApprover}
                  valueStyle={{ color: stats.withoutApprover > 0 ? "var(--color-danger)" : undefined }}
                />
              </Card>
            </Col>
          </Row>

          <Card
            className="page-panel table-card"
            title={
              <Space>
                <SettingOutlined />
                <span>User Management</span>
              </Space>
            }
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAddUser}
                >
                  Add User
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={fetchUsers}
                  loading={loading}
                >
                  Refresh
                </Button>
              </Space>
            }
          >
            <Table
              columns={columns}
              dataSource={users}
              rowKey="id"
              loading={loading}
              scroll={{ x: 1200 }}
              pagination={{
                pageSizeOptions: ['10', '20', '50', '100'],
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} users`,
              }}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'entities',
      label: 'Entities',
      children: <EntityManagement />,
    },
    ...(user?.role === "ADMIN"
      ? [
          {
            key: 'announcements',
            label: 'Announcements',
            children: <AnnouncementManagement />,
          },
        ]
      : []),
  ];

  return (
    <div className="page-shell page-shell--three-row settings-page">
      <section>
        <div className="page-kicker">Admin Settings</div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">
          Manage users, entities, exports, and approver assignments from one clear admin area.
        </p>
      </section>

      <Card
        className="page-panel"
        title={
          <Space>
            <DownloadOutlined />
            <span>Export Approved Leave Requests</span>
          </Space>
        }
      >
        <Space wrap>
          <DatePicker.RangePicker
            value={exportRange}
            onChange={(dates) => setExportRange(dates)}
            format="YYYY-MM-DD"
          />
          <Button
            type="primary"
            className="app-button-primary"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            loading={exporting}
          >
            Export to Excel
          </Button>
        </Space>
      </Card>

      <Card className="page-panel">
        <Tabs defaultActiveKey="users" items={tabItems} />
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

          <Form.Item
            label="Final Approver"
            name="final_approver"
            dependencies={["approver"]}
            tooltip="Optional second approval step"
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || value !== getFieldValue("approver")) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("Final approver must be different from first approver"));
                },
              }),
            ]}
          >
            <Select
              allowClear
              showSearch
              placeholder="Select a final approver"
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

      {/* Add User Modal */}
      <Modal
        title="Add New User"
        open={addModalVisible}
        onOk={handleCreateUser}
        onCancel={() => {
          setAddModalVisible(false);
          addForm.resetFields();
          setLocations([]);
          setDepartments([]);
        }}
        confirmLoading={creating}
        okText="Create User"
        width={700}
      >
        <Form form={addForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="First Name"
                name="first_name"
                rules={[{ required: true, message: "Please enter first name" }]}
              >
                <Input placeholder="John" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="Last Name"
                name="last_name"
                rules={[{ required: true, message: "Please enter last name" }]}
              >
                <Input placeholder="Doe" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="Email"
                name="email"
                rules={[
                  { required: true, message: "Please enter email" },
                  { type: "email", message: "Please enter a valid email" },
                ]}
              >
                <Input placeholder="john.doe@example.com" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item label="Employee Code" name="employee_code">
                <Input placeholder="EMP-001 (Optional)" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="Role"
                name="role"
                initialValue="EMPLOYEE"
                rules={[{ required: true, message: "Please select role" }]}
              >
                <Select>
                  <Select.Option value="EMPLOYEE">Employee</Select.Option>
                  <Select.Option value="MANAGER">Manager</Select.Option>
                  <Select.Option value="HR">HR</Select.Option>
                  <Select.Option value="ADMIN">Admin</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="Join Date"
                name="join_date"
                tooltip="Defaults to today if not specified"
              >
                <DatePicker style={{ width: "100%" }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={8}>
              <Form.Item
                label="Entity"
                name="entity"
                rules={[{ required: true, message: "Please select entity" }]}
              >
                <Select
                  placeholder="Select entity"
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
                  }
                  onChange={handleEntityChange}
                  options={entities.map((e) => ({
                    value: e.id,
                    label: e.entity_name,
                  }))}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item
                label="Location"
                name="location"
                rules={[{ required: true, message: "Please select location" }]}
              >
                <Select
                  placeholder={locations.length ? "Select location" : "Select entity first"}
                  disabled={locations.length === 0}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
                  }
                  onChange={handleLocationChange}
                  options={locations.map((loc) => ({
                    value: loc.id,
                    label: loc.location_name,
                  }))}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item
                label="Department"
                name="department"
                rules={[{ required: true, message: "Please select department" }]}
              >
                <Select
                  placeholder={departments.length ? "Select department" : "Select location first"}
                  disabled={departments.length === 0}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
                  }
                  options={departments.map((dept) => ({
                    value: dept.id,
                    label: dept.department_name,
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Approver"
            name="approver"
            rules={[{ required: true, message: "Please select an approver" }]}
          >
            <Select
              showSearch
              placeholder="Select an approver"
              filterOption={(input, option) =>
                (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              options={users
                .filter((u) => u.status === "ACTIVE")
                .map((u) => ({
                  value: u.id,
                  label: `${u.first_name} ${u.last_name}`.trim() || u.email,
                }))}
            />
          </Form.Item>

          <Form.Item
            label="Final Approver"
            name="final_approver"
            dependencies={["approver"]}
            tooltip="Optional. Leave empty for one-step approval."
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || value !== getFieldValue("approver")) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("Final approver must be different from first approver"));
                },
              }),
            ]}
          >
            <Select
              allowClear
              showSearch
              placeholder="Select a final approver"
              filterOption={(input, option) =>
                (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              options={users
                .filter((u) => u.status === "ACTIVE")
                .map((u) => ({
                  value: u.id,
                  label: `${u.first_name} ${u.last_name}`.trim() || u.email,
                }))}
            />
          </Form.Item>

          <Text type="secondary" style={{ fontSize: 12 }}>
            Note: Password will be auto-set to default. User will be required to change password on first login.
          </Text>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;
