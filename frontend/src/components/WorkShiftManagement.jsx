import { useEffect, useState } from "react";
import { Button, Card, Checkbox, Form, Input, Modal, Select, Space, Table, message } from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import http from "@api/http";
import { getDepartments, getEntities, getLocations, getWorkShifts } from "@api/authApi";

const asList = (data) => data?.results || data || [];

export default function WorkShiftManagement() {
  const [entities, setEntities] = useState([]);
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  // When checked, the shift is created in every active department of the selected entity
  const applyToAll = Form.useWatch("apply_to_all", form) || false;

  const loadShifts = async () => {
    setLoading(true);
    try {
      setShifts(asList(await getWorkShifts()));
    } catch {
      message.error("Failed to load work shifts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadShifts(); }, []);

  const openModal = async () => {
    form.resetFields();
    setLocations([]);
    setDepartments([]);
    setOpen(true);
    if (!entities.length) {
      try {
        setEntities(asList(await getEntities()));
      } catch {
        message.error("Failed to load entities");
      }
    }
  };
  const changeEntity = async (id) => {
    form.setFieldsValue({ location: undefined, department: undefined });
    setDepartments([]);
    try {
      setLocations(id ? asList(await getLocations(id)) : []);
    } catch {
      message.error("Failed to load locations");
    }
  };
  const changeLocation = async (id) => {
    form.setFieldsValue({ department: undefined });
    try {
      setDepartments(id ? asList(await getDepartments(id)) : []);
    } catch {
      message.error("Failed to load departments");
    }
  };

  const create = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const { data } = await http.post("/organizations/work-shifts/", {
        name: values.name,
        start_time: values.start_time,
        end_time: values.end_time,
        includes_weekends: values.includes_weekends || false,
        ...(values.apply_to_all
          ? { entity_id: values.entity, apply_to_all_departments: true }
          : { department_id: values.department }),
      });
      if (values.apply_to_all) {
        message.success(`Work shift created in ${data.created} department${data.created === 1 ? "" : "s"}`);
        if (data.skipped?.length) {
          message.info(`Skipped (name already exists): ${data.skipped.join(", ")}`);
        }
      } else {
        message.success("Work shift created");
      }
      setOpen(false);
      form.resetFields();
      await loadShifts();
    } catch (error) {
      if (!error.errorFields) {
        // Backend returns either {error: "..."} or DRF field errors like {name: ["..."]}
        const data = error.response?.data;
        const detail = data?.error || (data && Object.values(data).flat()[0]);
        message.error(detail || "Failed to create work shift");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Card
        className="page-panel table-card"
        title="Work Shifts"
        extra={<Space wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={openModal}>Add Shift</Button>
          <Button icon={<ReloadOutlined />} onClick={loadShifts} loading={loading}>Refresh</Button>
        </Space>}
      >
        <Table rowKey="id" dataSource={shifts} loading={loading} pagination={false} columns={[
          { title: "Entity", dataIndex: "entity_name", key: "entity_name", ellipsis: true },
          { title: "Department", dataIndex: "department_name", key: "department_name", ellipsis: true },
          { title: "Shift", dataIndex: "name", key: "name", ellipsis: true },
          { title: "Start", dataIndex: "start_time", key: "start_time", width: 100 },
          { title: "End", dataIndex: "end_time", key: "end_time", width: 100 },
          { title: "Weekends", dataIndex: "includes_weekends", key: "includes_weekends", width: 110, render: (value) => value ? "Yes" : "-" },
          { title: "Type", key: "type", width: 120, render: (_, row) => row.end_time <= row.start_time ? "Overnight" : "Day shift" },
        ]} />
      </Card>
      <Modal title="Add Work Shift" open={open} onOk={create} confirmLoading={saving} onCancel={() => setOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="entity" label="Entity" rules={[{ required: true, message: "Please select entity" }]}>
            <Select placeholder="Select entity" onChange={changeEntity}
              options={entities.map((item) => ({ value: item.id, label: item.entity_name }))} />
          </Form.Item>
          <Form.Item name="apply_to_all" valuePropName="checked">
            <Checkbox>Apply to all departments in this entity</Checkbox>
          </Form.Item>
          {!applyToAll && (
            <>
              <Form.Item name="location" label="Location" rules={[{ required: true, message: "Please select location" }]}>
                <Select placeholder={locations.length ? "Select location" : "Select entity first"} disabled={!locations.length} onChange={changeLocation}
                  options={locations.map((item) => ({ value: item.id, label: item.location_name }))} />
              </Form.Item>
              <Form.Item name="department" label="Department" rules={[{ required: true, message: "Please select department" }]}>
                <Select placeholder={departments.length ? "Select department" : "Select location first"} disabled={!departments.length}
                  options={departments.map((item) => ({ value: item.id, label: item.department_name }))} />
              </Form.Item>
            </>
          )}
          <Form.Item name="name" label="Shift name" rules={[{ required: true }]}><Input placeholder="Night Shift" /></Form.Item>
          <Form.Item name="start_time" label="Start time" rules={[{ required: true }]}><Input type="time" /></Form.Item>
          <Form.Item name="end_time" label="End time" rules={[{ required: true }]}><Input type="time" /></Form.Item>
          <Form.Item name="includes_weekends" valuePropName="checked">
            <Checkbox>Count weekends as working days</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
