import { useEffect, useState } from "react";
import { Alert, Button, Card, Checkbox, Empty, Form, Input, Modal, Popconfirm, Select, Space, Tag, message } from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { useAuth } from "@auth/authContext";
import http from "@api/http";
import { getDepartments, getEntities, getLocations, getWorkShifts } from "@api/authApi";
import "./WorkShiftManagement.css";

const asList = (data) => data?.results || data || [];
const TIME_OPTIONS = Array.from({ length: 24 }, (_, hour) => {
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return {
    value: `${String(hour).padStart(2, "0")}:00`,
    label: `${displayHour}:00 ${period}`,
  };
});

const formatTimeAmPm = (value) => {
  if (!value) return "";
  const [hourText, minute = "00"] = value.split(":");
  const hour = Number(hourText);
  return `${hour % 12 || 12}:${minute} ${hour >= 12 ? "PM" : "AM"}`;
};

const TimeSelect = (props) => (
  <Select
    {...props}
    showSearch
    optionFilterProp="label"
    options={TIME_OPTIONS}
  />
);

const SOC_ROTATION_DAYS = [
  { name: "Morning", start_time: "06:00", end_time: "14:00", is_working: true },
  { name: "Evening", start_time: "14:00", end_time: "22:00", is_working: true },
  { name: "Night", start_time: "22:00", end_time: "06:00", is_working: true },
  { name: "Off", is_working: false },
];

const getScheduleDays = (shift) => (
  shift.pattern_type === "ROTATING_CYCLE"
    ? shift.cycle_days?.length ? shift.cycle_days : SOC_ROTATION_DAYS
    : [{ name: "Fixed", start_time: shift.start_time, end_time: shift.end_time, is_working: true }]
);

const cycleFormValues = (days = SOC_ROTATION_DAYS) => ({
  morning_start_time: days[0]?.start_time || "06:00",
  morning_end_time: days[0]?.end_time || "14:00",
  evening_start_time: days[1]?.start_time || "14:00",
  evening_end_time: days[1]?.end_time || "22:00",
  night_start_time: days[2]?.start_time || "22:00",
  night_end_time: days[2]?.end_time || "06:00",
});

const buildCycleDays = (values) => [
  { name: "Morning", start_time: values.morning_start_time || "06:00", end_time: values.morning_end_time || "14:00", is_working: true },
  { name: "Evening", start_time: values.evening_start_time || "14:00", end_time: values.evening_end_time || "22:00", is_working: true },
  { name: "Night", start_time: values.night_start_time || "22:00", end_time: values.night_end_time || "06:00", is_working: true },
  { name: "Off", is_working: false },
];

const renderSchedule = (shift) => (
  <div className="work-shift-schedule">
    {getScheduleDays(shift).map((day, index) => (
      <Tag key={day.name + "-" + index} color={day.is_working === false ? "default" : "blue"}>
        {day.is_working === false
          ? "Off"
          : `${day.name} ${formatTimeAmPm(day.start_time)}-${formatTimeAmPm(day.end_time)}`}
      </Tag>
    ))}
  </div>
);

const groupWorkShifts = (shifts) => {
  const groups = new Map();
  shifts.forEach((shift) => {
    const groupId = shift.management_group_id || shift.id;
    const group = groups.get(groupId) || {
      id: groupId,
      representative: shift,
      entityIds: new Set(),
      entityNames: new Set(),
      locationKeys: new Set(),
      memberCount: 0,
    };
    group.entityIds.add(shift.entity_id);
    group.entityNames.add(shift.entity_name);
    group.locationKeys.add(`${shift.entity_name}:${shift.location_name || "Entity-wide"}`);
    group.memberCount += 1;
    groups.set(groupId, group);
  });
  return Array.from(groups.values());
};

export default function WorkShiftManagement() {
  const { user } = useAuth();
  const [entities, setEntities] = useState([]);
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingShift, setEditingShift] = useState(null);
  const [editingGroup, setEditingGroup] = useState(null);
  const [form] = Form.useForm();
  const applyToAll = Form.useWatch("apply_to_all", form) || false;
  const selectedEntityIds = Form.useWatch("entities", form) || [];
  const isMultiEntity = selectedEntityIds.length > 1;
  const patternType = Form.useWatch("pattern_type", form) || "FIXED_WEEKLY";
  const shiftGroups = groupWorkShifts(shifts);
  const canEditGroupEntities = user?.role === "ADMIN" && editingGroup?.entityIds.size > 1;

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

  useEffect(() => {
    loadShifts();
  }, []);

  const openModal = async () => {
    form.resetFields();
    form.setFieldsValue({ pattern_type: "FIXED_WEEKLY", ...cycleFormValues() });
    setEditingShift(null);
    setEditingGroup(null);
    setLocations([]);
    setDepartments([]);
    setOpen(true);
    try {
      const data = entities.length ? entities : asList(await getEntities());
      const availableEntities = user?.role === "HR"
        ? data.filter((item) => item.id === user.entity?.id)
        : data;
      setEntities(availableEntities);
      if (user?.role === "HR" && user.entity?.id) {
        form.setFieldValue("entities", [user.entity.id]);
        await changeEntities([user.entity.id]);
      }
    } catch {
      message.error("Failed to load entities");
    }
  };

  const openEditModal = async (group) => {
    const shift = group.representative;
    setEditingShift(shift);
    setEditingGroup(group);
    form.resetFields();
    form.setFieldsValue({
      entities: Array.from(group.entityIds),
      name: shift.name,
      pattern_type: shift.pattern_type || "FIXED_WEEKLY",
      start_time: shift.pattern_type === "ROTATING_CYCLE" ? undefined : shift.start_time,
      end_time: shift.pattern_type === "ROTATING_CYCLE" ? undefined : shift.end_time,
      includes_weekends: shift.includes_weekends,
      ...cycleFormValues(shift.cycle_days),
    });
    setOpen(true);
    try {
      const data = entities.length ? entities : asList(await getEntities());
      setEntities(user?.role === "HR"
        ? data.filter((item) => item.id === user.entity?.id)
        : data);
    } catch {
      message.error("Failed to load entities");
    }
  };

  const deleteShift = async (shift) => {
    try {
      await http.delete("/organizations/work-shifts/" + shift.id + "/");
      message.success("Work shift deleted");
      await loadShifts();
    } catch (error) {
      const data = error.response?.data;
      message.error(data?.error || "Failed to delete work shift");
    }
  };

  const changeEntities = async (ids) => {
    form.setFieldsValue({
      apply_to_all: ids.length > 1 ? false : form.getFieldValue("apply_to_all"),
      location: undefined,
      department: undefined,
    });
    setDepartments([]);
    if (ids.length !== 1) {
      setLocations([]);
      return;
    }
    try {
      setLocations(asList(await getLocations(ids[0])));
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
      const cycleDays = buildCycleDays(values);
      const payload = {
        name: values.name,
        pattern_type: values.pattern_type || "FIXED_WEEKLY",
        start_time: values.pattern_type === "ROTATING_CYCLE" ? cycleDays[0].start_time : values.start_time,
        end_time: values.pattern_type === "ROTATING_CYCLE" ? cycleDays[0].end_time : values.end_time,
        break_start_time: null,
        break_end_time: null,
        includes_weekends: values.pattern_type === "ROTATING_CYCLE" ? true : values.includes_weekends || false,
        cycle_days: values.pattern_type === "ROTATING_CYCLE" ? cycleDays : [],
      };
      const entityIds = values.entities || [];
      const isMultiEntitySubmission = entityIds.length > 1;
      const appliesToMultipleDepartments = isMultiEntitySubmission || values.apply_to_all;
      const { data } = editingShift
        ? await http.patch("/organizations/work-shifts/" + editingShift.id + "/", {
          ...payload,
          ...(canEditGroupEntities ? { entity_ids: entityIds } : {}),
        })
        : await http.post("/organizations/work-shifts/", {
          ...payload,
          ...(isMultiEntitySubmission
            ? { entity_ids: entityIds }
            : values.apply_to_all
              ? { entity_id: entityIds[0], apply_to_all_departments: true }
            : { department_id: values.department }),
        });

      if (!editingShift && appliesToMultipleDepartments) {
        message.success("Work shift created in " + data.created + " department" + (data.created === 1 ? "" : "s"));
        if (data.assigned_users) {
          message.info("Automatically assigned to " + data.assigned_users + " user" + (data.assigned_users === 1 ? "" : "s") + " without a work shift");
        }
        if (data.skipped?.length) {
          message.info("Skipped (name already exists): " + data.skipped.join(", "));
        }
      } else {
        message.success(editingShift ? "Work shift updated" : "Work shift created");
        if (editingShift && canEditGroupEntities) {
          message.info(
            `Added ${data.added_departments} and removed ${data.removed_departments} department shift${data.removed_departments === 1 ? "" : "s"}`
          );
        }
      }
      setOpen(false);
      setEditingShift(null);
      setEditingGroup(null);
      form.resetFields();
      await loadShifts();
    } catch (error) {
      if (!error.errorFields) {
        const data = error.response?.data;
        const detail = data?.error || (data && Object.values(data).flat()[0]);
        message.error(detail || "Failed to save work shift");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Card
        className="page-panel table-card work-shift-card"
        title="Work Shifts"
        extra={<Space wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={openModal}>Add Shift</Button>
          <Button icon={<ReloadOutlined />} onClick={loadShifts} loading={loading}>Refresh</Button>
        </Space>}
      >
        {shiftGroups.length ? (
          <div className="work-shift-list" aria-busy={loading}>
            {shiftGroups.map((group) => {
              const shift = group.representative;
              return (
              <article className="work-shift-item" key={group.id}>
                <div className="work-shift-main">
                  <div className="work-shift-title-row">
                    <strong className="work-shift-title">{shift.name}</strong>
                    <Tag color={shift.pattern_type === "ROTATING_CYCLE" ? "purple" : "green"}>
                      {shift.pattern_type === "ROTATING_CYCLE" ? "Rotating cycle" : "Fixed weekly"}
                    </Tag>
                  </div>
                  <div className="work-shift-meta">
                    <span>{Array.from(group.entityNames).join(", ")}</span>
                    <span>{group.locationKeys.size} location{group.locationKeys.size === 1 ? "" : "s"}</span>
                    <span>{group.memberCount} department{group.memberCount === 1 ? "" : "s"}</span>
                  </div>
                  {renderSchedule(shift)}
                </div>
                <div className="work-shift-actions">
                  <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(group)}>Edit</Button>
                  <Popconfirm title="Delete this work shift?" okText="Delete" okButtonProps={{ danger: true }} onConfirm={() => deleteShift(shift)}>
                    <Button size="small" danger icon={<DeleteOutlined />}>Delete</Button>
                  </Popconfirm>
                </div>
              </article>
              );
            })}
          </div>
        ) : (
          <Empty description={loading ? "Loading work shifts..." : "No work shifts configured"} />
        )}
      </Card>

      <Modal
        title={editingShift ? "Edit Work Shift" : "Add Work Shift"}
        open={open}
        onOk={create}
        confirmLoading={saving}
        onCancel={() => { setOpen(false); setEditingShift(null); setEditingGroup(null); }}
      >
        <Form form={form} layout="vertical">
          {(!editingShift || canEditGroupEntities) && (
            <Form.Item name="entities" label="Entity" rules={[{ required: true, message: "Please select at least one entity" }]}>
              <Select
                mode="multiple"
                placeholder="Select one or more entities"
                disabled={user?.role === "HR"}
                onChange={editingShift ? undefined : changeEntities}
                options={entities.map((item) => ({ value: item.id, label: item.entity_name }))}
              />
            </Form.Item>
          )}
          {!editingShift && !isMultiEntity && (
            <Form.Item name="apply_to_all" valuePropName="checked">
              <Checkbox>Apply to all departments in this entity</Checkbox>
            </Form.Item>
          )}
          {!editingShift && !isMultiEntity && !applyToAll && (
            <>
              <Form.Item name="location" label="Location" rules={[{ required: true, message: "Please select location" }]}>
                <Select
                  placeholder={locations.length ? "Select location" : "Select entity first"}
                  disabled={!locations.length}
                  onChange={changeLocation}
                  options={locations.map((item) => ({ value: item.id, label: item.location_name }))}
                />
              </Form.Item>
              <Form.Item name="department" label="Department" rules={[{ required: true, message: "Please select department" }]}>
                <Select
                  placeholder={departments.length ? "Select department" : "Select location first"}
                  disabled={!departments.length}
                  options={departments.map((item) => ({ value: item.id, label: item.department_name }))}
                />
              </Form.Item>
            </>
          )}
          <Form.Item name="name" label="Shift name" rules={[{ required: true }]}>
            <Input placeholder="SOC Rotation" />
          </Form.Item>
          <Form.Item name="pattern_type" label="Pattern" initialValue="FIXED_WEEKLY" rules={[{ required: true }]}>
            <Select
              onChange={(value) => {
                if (value === "ROTATING_CYCLE") {
                  form.setFieldsValue({ start_time: undefined, end_time: undefined, includes_weekends: true, ...cycleFormValues() });
                }
              }}
              options={[
                { value: "FIXED_WEEKLY", label: "Fixed weekly" },
                { value: "ROTATING_CYCLE", label: "SOC rotation: Morning, Evening, Night, Off" },
              ]}
            />
          </Form.Item>
          {patternType === "ROTATING_CYCLE" && (
            <>
              <Alert
                showIcon
                type="info"
                style={{ marginBottom: 16 }}
                message="Rotating cycle ignores weekdays/weekends. Leave balance is deducted only on cycle days marked Morning, Evening, or Night; Off days are skipped."
              />
              <div className="work-shift-cycle-editor">
                <div className="work-shift-cycle-row">
                  <strong>Morning</strong>
                  <Form.Item name="morning_start_time" rules={[{ required: true, message: "Required" }]}><TimeSelect /></Form.Item>
                  <span>to</span>
                  <Form.Item name="morning_end_time" rules={[{ required: true, message: "Required" }]}><TimeSelect /></Form.Item>
                </div>
                <div className="work-shift-cycle-row">
                  <strong>Evening</strong>
                  <Form.Item name="evening_start_time" rules={[{ required: true, message: "Required" }]}><TimeSelect /></Form.Item>
                  <span>to</span>
                  <Form.Item name="evening_end_time" rules={[{ required: true, message: "Required" }]}><TimeSelect /></Form.Item>
                </div>
                <div className="work-shift-cycle-row">
                  <strong>Night</strong>
                  <Form.Item name="night_start_time" rules={[{ required: true, message: "Required" }]}><TimeSelect /></Form.Item>
                  <span>to</span>
                  <Form.Item name="night_end_time" rules={[{ required: true, message: "Required" }]}><TimeSelect /></Form.Item>
                </div>
                <div className="work-shift-cycle-row work-shift-cycle-row--off">
                  <strong>Off</strong>
                  <span>No working hours deducted for this cycle day.</span>
                </div>
              </div>
            </>
          )}
          {patternType === "FIXED_WEEKLY" && (
            <>
              <Form.Item name="start_time" label="Start time" rules={[{ required: true }]}>
                <TimeSelect />
              </Form.Item>
              <Form.Item name="end_time" label="End time" rules={[{ required: true }]}>
                <TimeSelect />
              </Form.Item>
              <Form.Item name="includes_weekends" valuePropName="checked">
                <Checkbox>Treat Saturday and Sunday as working days</Checkbox>
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </>
  );
}
