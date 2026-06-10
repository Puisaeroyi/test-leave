import { useEffect, useState } from "react";
import { Button, Card, Form, Input, Modal, Select, Space, Table, message } from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import http from "@api/http";
import { getDepartments, getEntities, getLocations, getWorkShifts } from "@api/authApi";

export default function WorkShiftManagement() {
  const [entities, setEntities] = useState([]);
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [entityId, setEntityId] = useState();
  const [locationId, setLocationId] = useState();
  const [departmentId, setDepartmentId] = useState();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => { getEntities().then((data) => setEntities(data.results || data)); }, []);

  const loadShifts = async (id = departmentId) => setShifts(id ? await getWorkShifts(id) : []);
  const changeEntity = async (id) => {
    setEntityId(id); setLocationId(); setDepartmentId(); setDepartments([]); setShifts([]);
    setLocations(id ? await getLocations(id) : []);
  };
  const changeLocation = async (id) => {
    setLocationId(id); setDepartmentId(); setShifts([]);
    setDepartments(id ? await getDepartments(id) : []);
  };
  const changeDepartment = async (id) => {
    setDepartmentId(id);
    await loadShifts(id);
  };
  const create = async () => {
    try {
      const values = await form.validateFields();
      await http.post("/organizations/work-shifts/", { ...values, department_id: departmentId });
      message.success("Work shift created");
      setOpen(false); form.resetFields(); await loadShifts();
    } catch (error) {
      if (!error.errorFields) message.error(error.response?.data?.error || "Failed to create work shift");
    }
  };

  return (
    <>
      <Card
        className="page-panel table-card"
        title="Work Shifts"
        extra={<Space wrap>
          <Select placeholder="Entity" value={entityId} onChange={changeEntity} style={{ width: 170 }}
            options={entities.map((item) => ({ value: item.id, label: item.entity_name }))} />
          <Select placeholder="Location" value={locationId} onChange={changeLocation} disabled={!entityId} style={{ width: 170 }}
            options={locations.map((item) => ({ value: item.id, label: item.location_name }))} />
          <Select placeholder="Department" value={departmentId} onChange={changeDepartment} disabled={!locationId} style={{ width: 190 }}
            options={departments.map((item) => ({ value: item.id, label: item.department_name }))} />
          <Button type="primary" icon={<PlusOutlined />} disabled={!departmentId} onClick={() => setOpen(true)}>Add Shift</Button>
          <Button icon={<ReloadOutlined />} disabled={!departmentId} onClick={() => loadShifts()}>Refresh</Button>
        </Space>}
      >
        <Table rowKey="id" dataSource={shifts} pagination={false} columns={[
          { title: "Shift", dataIndex: "name", key: "name" },
          { title: "Start", dataIndex: "start_time", key: "start_time", width: 120 },
          { title: "End", dataIndex: "end_time", key: "end_time", width: 120 },
          { title: "Type", key: "type", width: 140, render: (_, row) => row.end_time <= row.start_time ? "Overnight" : "Day shift" },
        ]} />
      </Card>
      <Modal title="Add Work Shift" open={open} onOk={create} onCancel={() => setOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Shift name" rules={[{ required: true }]}><Input placeholder="Night Shift" /></Form.Item>
          <Form.Item name="start_time" label="Start time" rules={[{ required: true }]}><Input type="time" /></Form.Item>
          <Form.Item name="end_time" label="End time" rules={[{ required: true }]}><Input type="time" /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
