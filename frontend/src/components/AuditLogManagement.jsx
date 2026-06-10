import { useCallback, useEffect, useState } from "react";
import { Button, Card, Descriptions, Empty, Modal, Select, Space, Table, Tag, Typography, message } from "antd";
import { EyeOutlined, ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getAuditLogs } from "@api/auditApi";
import { getAllUsers } from "@api/userApi";

const { Text } = Typography;

const actionColors = {
  CREATE: "green",
  UPDATE: "blue",
  DELETE: "red",
  APPROVE: "cyan",
  REJECT: "volcano",
  GENERATE: "purple",
  PUBLISH: "geekblue",
  UNPUBLISH: "orange",
  SPLIT_SCOPE: "magenta",
};

const actions = Object.keys(actionColors);
const entityTypes = [
  "APIRequest",
  "LeaveRequest",
  "User",
  "LeaveBalance",
  "Entity",
  "Location",
  "Department",
  "HolidayCalendar",
  "PublicHoliday",
];

export default function AuditLogManagement() {
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [action, setAction] = useState();
  const [entityType, setEntityType] = useState();
  const [ordering, setOrdering] = useState("newest");
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [data, usersData] = await Promise.all([
        getAuditLogs({
          page,
          page_size: pageSize,
          action,
          entity_type: entityType,
          ordering,
        }),
        getAllUsers(),
      ]);
      const users = Array.isArray(usersData) ? usersData : usersData?.results || [];
      const userEmails = new Map(users.map((user) => [String(user.id), user.email]));
      setLogs((data.results || []).map((log) => ({
        ...log,
        changes: (log.changes || []).map((change) => ({
          ...change,
          before: resolveUserReference(change.before, userEmails),
          after: resolveUserReference(change.after, userEmails),
        })),
      })));
      setCount(data.count || 0);
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [action, entityType, ordering, page, pageSize]);

  useEffect(() => {
    load();
  }, [load]);

  const columns = [
    {
      title: "Time",
      dataIndex: "created_at",
      key: "created_at",
      width: 170,
      render: (value) => dayjs(value).format("YYYY-MM-DD HH:mm:ss"),
    },
    { title: "Performed by", dataIndex: "user_email", key: "user_email", width: 210 },
    {
      title: "Action",
      dataIndex: "action",
      key: "action",
      width: 120,
      render: (value, row) => <Tag color={actionColors[value]}>{row.action_label || value}</Tag>,
    },
    {
      title: "Activity",
      dataIndex: "summary",
      key: "summary",
      render: (value, row) => (
        <div>
          <div>{value}</div>
          <Text type="secondary">{row.target_label}</Text>
        </div>
      ),
    },
    {
      title: "Detail",
      key: "detail",
      width: 75,
      render: (_, row) => <Button size="small" icon={<EyeOutlined />} onClick={() => setSelected(row)} />,
    },
  ];

  return (
    <>
      <Card
        className="page-panel table-card"
        title="Audit Logs"
        extra={
          <Space wrap>
            <Select
              value={ordering}
              onChange={(value) => { setOrdering(value); setPage(1); }}
              options={[
                { value: "newest", label: "Newest first" },
                { value: "oldest", label: "Oldest first" },
              ]}
              style={{ width: 145 }}
            />
            <Select
              allowClear
              placeholder="Action"
              value={action}
              onChange={(value) => { setAction(value); setPage(1); }}
              options={actions.map((value) => ({ value, label: value }))}
              style={{ width: 140 }}
            />
            <Select
              allowClear
              placeholder="Type"
              value={entityType}
              onChange={(value) => { setEntityType(value); setPage(1); }}
              options={entityTypes.map((value) => ({ value, label: value }))}
              style={{ width: 170 }}
            />
            <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
          </Space>
        }
      >
        <Table
          className="audit-log-table"
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1120, y: 460 }}
          tableLayout="fixed"
          pagination={{
            current: page,
            pageSize,
            total: count,
            showSizeChanger: true,
            pageSizeOptions: ["10", "25", "50", "100"],
            showQuickJumper: true,
            hideOnSinglePage: false,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} audit logs`,
            position: ["bottomRight"],
            onChange: (nextPage, nextSize) => {
              setPage(nextSize === pageSize ? nextPage : 1);
              setPageSize(nextSize);
            },
          }}
        />
      </Card>

      <Modal title="Audit Log Detail" open={Boolean(selected)} onCancel={() => setSelected(null)} footer={null} width={820}>
        {selected && (
          <Space direction="vertical" size={20} style={{ width: "100%" }}>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Activity" span={2}>{selected.summary}</Descriptions.Item>
              <Descriptions.Item label="Performed by">{selected.user_email}</Descriptions.Item>
              <Descriptions.Item label="Time">{dayjs(selected.created_at).format("YYYY-MM-DD HH:mm:ss")}</Descriptions.Item>
              <Descriptions.Item label="Target" span={2}>{selected.target_label}</Descriptions.Item>
              <Descriptions.Item label="Action">{selected.action_label}</Descriptions.Item>
              <Descriptions.Item label="Type">{selected.entity_label}</Descriptions.Item>
            </Descriptions>

            <div>
              <Text strong>Changes</Text>
              {selected.changes?.length ? (
                <Table
                  style={{ marginTop: 10 }}
                  size="small"
                  pagination={false}
                  rowKey="field"
                  dataSource={selected.changes}
                  columns={[
                    { title: "Field", dataIndex: "field", key: "field", width: 170 },
                    { title: "Before", dataIndex: "before", key: "before", render: renderValue },
                    { title: "After", dataIndex: "after", key: "after", render: renderValue },
                  ]}
                />
              ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No field-level changes recorded" />}
            </div>
          </Space>
        )}
      </Modal>
    </>
  );
}

function renderValue(value) {
  if (value === null || value === undefined || value === "") return <Text type="secondary">-</Text>;
  if (typeof value === "object") return <Text code>{JSON.stringify(value)}</Text>;
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) {
    return dayjs(value).format("YYYY-MM-DD HH:mm:ss");
  }
  return String(value);
}

function resolveUserReference(value, userEmails) {
  if (typeof value !== "string") return value;
  return userEmails.get(value) || value;
}
