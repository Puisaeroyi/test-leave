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
  deleteHolidayCalendar,
  generateHolidayCalendars,
  getHolidayCalendar,
  getHolidayCalendars,
  publishHolidayCalendar,
  unpublishHolidayCalendar,
  updateHoliday,
} from "@api/holidayApi";

const statusColor = { DRAFT: "gold", PUBLISHED: "green", ARCHIVED: "default" };
const holidayTypeOptions = [
  { value: "STATUTORY", label: "Official holiday" },
  { value: "OBSERVED", label: "Observed day off" },
  { value: "COMPENSATORY", label: "Compensatory day off" },
  { value: "COMPANY", label: "Company holiday" },
];
const holidayYears = Array.from({ length: 10 }, (_, index) => 2026 + index);

export default function HolidayManagement() {
  const [calendars, setCalendars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [year, setYear] = useState(dayjs().year());
  const [selected, setSelected] = useState(null);
  const [holidayModal, setHolidayModal] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState(null);
  const [generating, setGenerating] = useState(false);
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
    setGenerating(true);
    try {
      const created = await generateHolidayCalendars(year);
      message.success(created.length ? `Created ${created.length} Draft calendars` : "No new calendars to create");
      await load();
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to generate calendars");
    } finally {
      setGenerating(false);
    }
  };

  const publish = (calendar) => {
    Modal.confirm({
      title: "Publish holiday calendar?",
      content: "Published holidays become visible in employee calendars immediately.",
      okText: "Publish",
      onOk: async () => {
        try {
          await publishHolidayCalendar(calendar.id);
          message.success("Holiday calendar published");
          setSelected(null);
          await load();
        } catch (error) {
          message.error(error.response?.data?.error || "Failed to publish calendar");
          throw error;
        }
      },
    });
  };

  const unpublish = (calendar) => {
    Modal.confirm({
      title: "Unpublish holiday calendar?",
      content: "The calendar will return to Draft and disappear from employee calendars.",
      okText: "Unpublish",
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await unpublishHolidayCalendar(calendar.id);
          message.success("Calendar returned to Draft");
          setSelected(null);
          await load();
        } catch (error) {
          message.error(error.response?.data?.error || "Failed to unpublish calendar");
          throw error;
        }
      },
    });
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

  const removeCalendar = async (calendar) => {
    try {
      await deleteHolidayCalendar(calendar.id);
      if (selected?.id === calendar.id) setSelected(null);
      message.success("Holiday calendar deleted");
      await load();
    } catch (error) {
      message.error(error.response?.data?.error || "Failed to delete holiday calendar");
    }
  };

  const calendarColumns = [
    { title: "Calendar", dataIndex: "name", key: "name", width: 240 },
    { title: "Country", dataIndex: "country_code", key: "country_code", width: 70 },
    { title: "Entity", dataIndex: "entity_name", key: "entity_name", width: 140 },
    { title: "Location", dataIndex: "location_name", key: "location_name", width: 140, render: (v) => v || "All locations" },
    { title: "Days", dataIndex: "holiday_count", key: "holiday_count", width: 75 },
    { title: "Status", dataIndex: "status", key: "status", width: 90, render: (v) => <Tag color={statusColor[v]}>{v}</Tag> },
    {
      title: "Action",
      key: "action",
      width: 130,
      render: (_, row) => (
        <Space size={6} onClick={(event) => event.stopPropagation()}>
          <Button size="small" onClick={() => openCalendar(row)}>
            Manage
          </Button>
          {row.status === "DRAFT" && (
            <Popconfirm
              title="Delete holiday calendar?"
              description="This will delete all holidays in this Draft calendar."
              okText="Delete"
              okButtonProps={{ danger: true }}
              onConfirm={() => removeCalendar(row)}
            >
              <Button size="small" danger icon={<DeleteOutlined />} aria-label="Delete holiday calendar" />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];
  const entityOptions = Array.from(
    new Map(calendars.map((calendar) => [calendar.entity_id, calendar.entity_name]))
  ).map(([value, label]) => ({ value, label }));

  const holidayColumns = [
    { title: "Date", dataIndex: "date", key: "date", width: 115 },
    { title: "Holiday", dataIndex: "holiday_name", key: "holiday_name", width: 260 },
    {
      title: "Range",
      key: "range",
      width: 210,
      render: (_, row) => row.start_date === row.end_date ? row.start_date : `${row.start_date} to ${row.end_date}`,
    },
    { title: "Type", dataIndex: "holiday_type_label", key: "holiday_type_label", width: 180 },
    { title: "Weekend", dataIndex: "is_weekend", key: "is_weekend", width: 95, render: (value) => value ? "Yes" : "-" },
    {
      title: "Action",
      key: "action",
      width: 90,
      render: (_, row) => selected?.status === "DRAFT" && (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openHoliday({ ...row, id: row.holiday_id })} />
          <Popconfirm title="Delete holiday?" onConfirm={() => removeHoliday({ ...row, id: row.holiday_id })}>
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
              options={holidayYears.map((value) => ({ value, label: value }))}
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
            <Button type="primary" icon={<PlusOutlined />} onClick={generate} loading={generating}>Generate Drafts</Button>
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
        className="holiday-detail-modal"
        title={selected?.name}
        open={Boolean(selected)}
        onCancel={() => setSelected(null)}
        footer={
          selected && (
            <Space>
              {selected.status === "DRAFT" && <Button icon={<PlusOutlined />} onClick={() => openHoliday()}>Add Holiday</Button>}
              {selected.status === "DRAFT"
                ? <Button type="primary" onClick={() => publish(selected)}>Publish</Button>
                : <Button danger onClick={() => unpublish(selected)}>Unpublish</Button>}
              <Button onClick={() => setSelected(null)}>Close</Button>
            </Space>
          )
        }
        style={{ top: 32 }}
        styles={{ body: { maxHeight: "calc(100dvh - 220px)", overflowY: "auto" } }}
        width="calc(100vw - 48px)"
      >
        <Table
          className="holiday-detail-table"
          columns={holidayColumns}
          dataSource={selected?.holiday_days || []}
          rowKey="id"
          pagination={false}
          tableLayout="fixed"
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
            <Select options={holidayTypeOptions} />
          </Form.Item>
          <Form.Item name="source_note" label="Source / note">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
