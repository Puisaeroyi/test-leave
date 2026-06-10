import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  message,
} from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import {
  addHoliday,
  deleteHoliday,
  generateHolidayCalendars,
  getHolidayCalendar,
  getHolidayCalendars,
  previewHolidayCalendarGeneration,
  previewPublishHolidayCalendar,
  previewUnpublishHolidayCalendar,
  publishHolidayCalendar,
  unpublishHolidayCalendar,
  updateHoliday,
} from "@api/holidayApi";

const statusColor = { DRAFT: "gold", PUBLISHED: "green", ARCHIVED: "default" };

export default function HolidayManagement() {
  const [calendars, setCalendars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [year, setYear] = useState(dayjs().year());
  const [selected, setSelected] = useState(null);
  const [holidayModal, setHolidayModal] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState(null);
  const [generationPreview, setGenerationPreview] = useState(null);
  const [countryOverrides, setCountryOverrides] = useState({});
  const [countryFilter, setCountryFilter] = useState();
  const [statusFilter, setStatusFilter] = useState();
  const [entityFilter, setEntityFilter] = useState();
  const [form] = Form.useForm();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCalendars(await getHolidayCalendars({
        year,
        country_code: countryFilter,
        status: statusFilter,
        entity_id: entityFilter,
      }));
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to load holiday calendars");
    } finally {
      setLoading(false);
    }
  }, [countryFilter, entityFilter, statusFilter, year]);

  useEffect(() => {
    load();
  }, [load]);

  const openCalendar = async (calendar) => {
    setSelected(await getHolidayCalendar(calendar.id));
  };

  const generate = async () => {
    try {
      const preview = await previewHolidayCalendarGeneration(year, countryOverrides);
      setGenerationPreview(preview);
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to preview calendars");
    }
  };

  const confirmGenerate = async () => {
    try {
      const created = await generateHolidayCalendars(year, countryOverrides);
      message.success(created.length ? `Created ${created.length} Draft calendars` : "No new calendars to create");
      setGenerationPreview(null);
      await load();
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to generate calendars");
    }
  };

  const publish = async (calendar) => {
    try {
      const preview = await previewPublishHolidayCalendar(calendar.id);
      Modal.confirm({
        title: "Publish holiday calendar?",
        width: 720,
        content: <ImpactSummary preview={preview} mode="publish" />,
        okText: "Publish",
        onOk: async () => {
          const result = await publishHolidayCalendar(calendar.id);
          message.success(`Published; recalculated ${result.affected_requests} leave requests`);
          setSelected(null);
          await load();
        },
      });
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to publish calendar");
    }
  };

  const previewUnpublish = async (calendar) => {
    try {
      const preview = await previewUnpublishHolidayCalendar(calendar.id);
      Modal.confirm({
        title: "Unpublish holiday calendar?",
        width: 720,
        content: <ImpactSummary preview={preview} mode="unpublish" />,
        okText: "Unpublish",
        okButtonProps: { danger: true, disabled: preview.blocked },
        onOk: async () => {
          await unpublishHolidayCalendar(calendar.id, preview.preview_token);
          message.success("Calendar returned to Draft");
          setSelected(null);
          await load();
        },
      });
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to preview unpublish");
    }
  };

  const openHoliday = (holiday = null) => {
    setEditingHoliday(holiday);
    form.setFieldsValue({
      holiday_name: holiday?.holiday_name,
      date_range: holiday ? [dayjs(holiday.start_date), dayjs(holiday.end_date)] : null,
      holiday_type: holiday?.holiday_type || "COMPANY",
      source_note: holiday?.source_note || "",
    });
    setHolidayModal(true);
  };

  const saveHoliday = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        holiday_name: values.holiday_name,
        start_date: values.date_range[0].format("YYYY-MM-DD"),
        end_date: values.date_range[1].format("YYYY-MM-DD"),
        holiday_type: values.holiday_type,
        source_note: values.source_note || "",
      };
      if (editingHoliday) await updateHoliday(editingHoliday.id, payload);
      else await addHoliday(selected.id, payload);
      setHolidayModal(false);
      setSelected(await getHolidayCalendar(selected.id));
      message.success("Holiday saved");
    } catch (error) {
      if (!error.errorFields) message.error(error.response?.data?.error || "Failed to save holiday");
    }
  };

  const removeHoliday = async (holiday) => {
    await deleteHoliday(holiday.id);
    setSelected(await getHolidayCalendar(selected.id));
  };

  const calendarColumns = [
    { title: "Calendar", dataIndex: "name", key: "name", width: 240 },
    { title: "Country", dataIndex: "country_code", key: "country_code", width: 70 },
    { title: "Entity", dataIndex: "entity_name", key: "entity_name", width: 140 },
    { title: "Location", dataIndex: "location_name", key: "location_name", width: 140, render: (v) => v || "All locations" },
    { title: "Holidays", dataIndex: "holiday_count", key: "holiday_count", width: 75 },
    { title: "Status", dataIndex: "status", key: "status", width: 90, render: (v) => <Tag color={statusColor[v]}>{v}</Tag> },
    {
      title: "Action",
      key: "action",
      width: 90,
      render: (_, row) => (
        <Button
          size="small"
          onClick={(event) => {
            event.stopPropagation();
            openCalendar(row);
          }}
        >
          Manage
        </Button>
      ),
    },
  ];
  const entityOptions = Array.from(
    new Map(calendars.map((calendar) => [calendar.entity_id, calendar.entity_name]))
  ).map(([value, label]) => ({ value, label }));

  const holidayColumns = [
    { title: "Holiday", dataIndex: "holiday_name", key: "holiday_name", width: 260 },
    { title: "From", dataIndex: "start_date", key: "start_date", width: 115 },
    { title: "To", dataIndex: "end_date", key: "end_date", width: 115 },
    { title: "Type", dataIndex: "holiday_type", key: "holiday_type", width: 130 },
    {
      title: "Action",
      key: "action",
      width: 90,
      render: (_, row) => selected?.status === "DRAFT" && (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openHoliday(row)} />
          <Popconfirm title="Delete holiday?" onConfirm={() => removeHoliday(row)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Card
        className="page-panel table-card holiday-management-card"
        title="Holiday Calendars"
        extra={
          <Space className="holiday-management-toolbar" wrap>
            <Select
              value={year}
              onChange={setYear}
              options={[2026, 2027].map((value) => ({ value, label: value }))}
              style={{ width: 100 }}
            />
            <Select
              allowClear
              placeholder="Country"
              value={countryFilter}
              onChange={setCountryFilter}
              options={[
                { value: "US", label: "United States" },
                { value: "VN", label: "Vietnam" },
              ]}
              style={{ width: 145 }}
            />
            <Select
              allowClear
              placeholder="Status"
              value={statusFilter}
              onChange={setStatusFilter}
              options={["DRAFT", "PUBLISHED", "ARCHIVED"].map((value) => ({ value, label: value }))}
              style={{ width: 130 }}
            />
            <Select
              allowClear
              placeholder="Entity"
              value={entityFilter}
              onChange={setEntityFilter}
              options={entityOptions}
              style={{ width: 170 }}
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={generate}>Generate Drafts</Button>
            <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
          </Space>
        }
      >
        <Table
          className="holiday-management-table"
          columns={calendarColumns}
          dataSource={calendars}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1050 }}
          tableLayout="fixed"
          onRow={(row) => ({
            onClick: () => openCalendar(row),
            style: { cursor: "pointer" },
          })}
        />
      </Card>

      <Modal
        title={selected?.name}
        open={Boolean(selected)}
        onCancel={() => setSelected(null)}
        footer={
          selected && (
            <Space>
              {selected.status === "DRAFT" && <Button icon={<PlusOutlined />} onClick={() => openHoliday()}>Add Holiday</Button>}
              {selected.status === "DRAFT"
                ? <Button type="primary" onClick={() => publish(selected)}>Publish</Button>
                : <Button danger onClick={() => previewUnpublish(selected)}>Preview Unpublish</Button>}
              <Button onClick={() => setSelected(null)}>Close</Button>
            </Space>
          )
        }
        width={900}
      >
        <Table columns={holidayColumns} dataSource={selected?.holidays || []} rowKey="id" pagination={false} scroll={{ x: 750 }} />
      </Modal>

      <Modal
        title={`Review ${year} country mapping`}
        open={Boolean(generationPreview)}
        onOk={confirmGenerate}
        onCancel={() => setGenerationPreview(null)}
        okText="Create Draft Calendars"
        width={850}
      >
        <Table
          rowKey="id"
          pagination={false}
          dataSource={(generationPreview || []).flatMap((entity) =>
            entity.locations.map((location) => ({ ...location, entity_name: entity.entity_name }))
          )}
          columns={[
            { title: "Entity", dataIndex: "entity_name", key: "entity_name" },
            { title: "Location", dataIndex: "name", key: "name" },
            { title: "Current country", dataIndex: "country", key: "country" },
            {
              title: "Holiday calendar",
              dataIndex: "country_code",
              key: "country_code",
              render: (value, row) => (
                <Select
                  value={countryOverrides[row.id] || value}
                  placeholder="Select country"
                  style={{ width: 170 }}
                  options={[
                    { value: "US", label: "United States" },
                    { value: "VN", label: "Vietnam" },
                  ]}
                  onChange={(countryCode) =>
                    setCountryOverrides((current) => ({ ...current, [row.id]: countryCode }))
                  }
                />
              ),
            },
          ]}
        />
      </Modal>

      <Modal
        className="holiday-form-modal"
        title={editingHoliday ? "Edit Holiday" : "Add Company Holiday"}
        open={holidayModal}
        onOk={saveHoliday}
        onCancel={() => setHolidayModal(false)}
        style={{ top: 24 }}
        styles={{ body: { maxHeight: "calc(100dvh - 190px)", overflowY: "auto" } }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="holiday_name" label="Holiday name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="date_range" label="Date range" rules={[{ required: true }]}>
            <DatePicker.RangePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="holiday_type" label="Type" rules={[{ required: true }]}>
            <Select options={["STATUTORY", "OBSERVED", "COMPENSATORY", "COMPANY"].map((value) => ({ value, label: value }))} />
          </Form.Item>
          <Form.Item name="source_note" label="Source / note">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

function ImpactSummary({ preview, mode }) {
  const changes = preview?.changes || [];
  const isPublish = mode === "publish";
  return (
    <div style={{ marginTop: 12 }}>
      <p>
        <strong>{preview?.affected_requests || 0}</strong> Pending or Approved leave requests
        will be recalculated.
      </p>
      {preview?.blocked && (
        <p style={{ color: "var(--color-danger)" }}>
          Unpublish is blocked because {preview.insufficient_balances.length} employees have insufficient balance.
        </p>
      )}
      {changes.length > 0 && (
        <Table
          size="small"
          pagination={false}
          rowKey="id"
          dataSource={changes}
          scroll={{ y: 260 }}
          columns={[
            { title: "Employee", dataIndex: "user_email", key: "user_email" },
            { title: "Status", dataIndex: "status", key: "status", width: 100 },
            { title: "Old", dataIndex: "old_hours", key: "old_hours", width: 70 },
            { title: "New", dataIndex: "new_hours", key: "new_hours", width: 70 },
            {
              title: isPublish ? "Refund" : "Additional",
              dataIndex: isPublish ? "refunded_hours" : "additional_hours",
              key: "delta",
              width: 95,
            },
          ]}
        />
      )}
    </div>
  );
}
