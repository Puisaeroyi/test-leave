import { useState, useEffect } from "react";
import {
  Modal,
  Steps,
  Typography,
  Form,
  Select,
  DatePicker,
  Radio,
  Input,
  Upload,
  Button,
  Card,
  Space,
  Divider,
  Tag,
  Result,
  message,
} from "antd";
import {
  UploadOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { getLeaveCategories, uploadFile } from "../api/dashboardApi";
import { getApplicableHolidays } from "../api/holidayApi";
import { calculateHourRange, inferCustomHourOffsets } from "../lib/time-utils";
import { useAuth } from "@auth/authContext";

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

// Whole-hour options for business hours 6 AM–6 PM, labelled in AM/PM
// (e.g. "09:00 AM"). Value is the 0-23 hour.
const HOUR_OPTIONS = Array.from({ length: 24 }, (_, index) => {
  const hour = (6 + index) % 24;
  return { value: hour, label: dayjs().hour(hour).minute(0).format("hh:00 A") };
});

// Single-column hour chooser used for custom-hour leave. A plain Select selects
// and closes on one click (no OK button, no lingering panel) while still feeding
// Form.Item a dayjs value so downstream `.format("HH:mm")`/`.diff()` keep working.
function HourSelect({ value, onChange, ...rest }) {
  return (
    <Select
      {...rest}
      style={{ width: 132 }}
      placeholder="Select hour"
      value={value ? value.hour() : undefined}
      onChange={(hour) =>
        onChange?.(dayjs().hour(hour).minute(0).second(0).millisecond(0))
      }
      options={HOUR_OPTIONS}
    />
  );
}

export default function NewLeaveRequestModal({
  open,
  onCancel,
  onSubmit,
  balances = [],
  initialDate = null, // Pre-selected date from calendar click
}) {
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [form] = Form.useForm();
  const [confirmData, setConfirmData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [categories, setCategories] = useState([]);

  // Pre-fill date from calendar click
  useEffect(() => {
    if (open && initialDate) {
      form.setFieldsValue({ date: [initialDate, initialDate] });
    }
  }, [open, initialDate, form]);

  const values = Form.useWatch([], form);
  const leaveCategory = Form.useWatch("leaveCategory", form);
  const selectedCategory = categories.find((category) => category.id === leaveCategory);
  const selectedBucket = selectedCategory?.balanceBucket || null;
  const sameDay = values?.date && values.date[0]?.isSame(values.date[1], "day");
  const dayType = values?.dayType || "full";

  // Progressive gating: each field unlocks only after the prior one is set,
  // so the form fills in order (Category -> Date -> the rest).
  const categoryChosen = !!leaveCategory;
  const dateChosen = !!(values?.date && values.date[0] && values.date[1]);

  useEffect(() => {
    if (!open) return;

    let active = true;
    getLeaveCategories()
      .then((data) => {
        if (active) setCategories(data);
      })
      .catch(() => {
        if (active) message.error("Failed to load leave categories");
      });

    return () => {
      active = false;
    };
  }, [open]);

  // SICK allows up to 2 weeks retroactive, VACATION requires 3-day advance, NONE has no restriction.
  const minLeaveDate =
    selectedBucket === "SICK"
      ? dayjs().subtract(14, "day").startOf("day")
      : selectedBucket === "VACATION"
      ? dayjs().add(3, "day").startOf("day")
      : null;

  const disabledDate = (current) => {
    if (!leaveCategory || !minLeaveDate) return false;
    return current && current < minLeaveDate;
  };

  // Changing the category can tighten the date rule (e.g. SICK -> VACATION's
  // 3-day advance). Clear an already-picked date that no longer qualifies so the
  // user must reselect a valid one. Keyed on the category, not the dayjs object.
  useEffect(() => {
    if (!minLeaveDate) return;
    const date = form.getFieldValue("date");
    const invalid =
      date &&
      (date[0]?.isBefore(minLeaveDate, "day") ||
        date[1]?.isBefore(minLeaveDate, "day"));
    if (invalid) {
      form.setFieldsValue({ date: undefined, startTime: undefined, endTime: undefined });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leaveCategory]);

  const calculateHours = (start, end) => {
    if (!start || !end) return 0;
    return calculateHourRange(start.hour(), end.hour());
  };

  // Calculate working days using the user's published holiday calendar.
  const countWorkingDays = (startDate, endDate, holidays = []) => {
    if (!startDate || !endDate) return 0;
    const holidayDates = new Set();
    holidays.forEach((holiday) => {
      let current = dayjs(holiday.start_date);
      const holidayEnd = dayjs(holiday.end_date);
      while (current.isBefore(holidayEnd, "day") || current.isSame(holidayEnd, "day")) {
        holidayDates.add(current.format("YYYY-MM-DD"));
        current = current.add(1, "day");
      }
    });
    let count = 0;
    let current = startDate.startOf("day");
    const end = endDate.startOf("day");

    while (current.isBefore(end) || current.isSame(end, "day")) {
      const dayOfWeek = current.day(); // 0=Sunday, 6=Saturday
      if (
        dayOfWeek !== 0 &&
        dayOfWeek !== 6 &&
        !holidayDates.has(current.format("YYYY-MM-DD"))
      ) {
        count++;
      }
      current = current.add(1, "day");
    }
    return count;
  };

  const previewHours =
    sameDay && dayType === "custom"
      ? calculateHours(values?.startTime, values?.endTime)
      : 0;

  const handleContinue = async () => {
    const data = await form.validateFields();
    let hours = 0;

    if (sameDay && data.dayType === "custom") {
      hours = calculateHours(data.startTime, data.endTime);

      if (hours > 8) {
        Modal.warning({
          title: "Invalid working hours",
          content: "Custom leave cannot exceed 8 hours per day.",
        });
        return;
      }

      if (hours <= 0) {
        Modal.warning({
          title: "Invalid time range",
          content: "Start time and end time must be different.",
        });
        return;
      }
    } else {
      const holidays = await getApplicableHolidays(data.date[0].year());
      const workingDays = countWorkingDays(data.date[0], data.date[1], holidays);
      hours = workingDays * 8;
    }

    const category = categories.find((item) => item.id === data.leaveCategory);
    const balanceBucket = category?.balanceBucket || "NONE";
    const selectedBalance = balanceBucket === "NONE"
      ? null
      : balances.find((balance) => balance.type === balanceBucket);

    setConfirmData({
      ...data,
      ...(sameDay && data.dayType === "custom"
        ? inferCustomHourOffsets(data.startTime.hour(), data.endTime.hour(), user?.work_shift)
        : {}),
      categoryName: category?.name || "Leave",
      balanceBucket,
      totalHours: hours,
      remainingHours: selectedBalance?.remaining_hours ?? null,
      allocated_hours: selectedBalance?.allocated_hours ?? null,
    });
    setStep(1);
  };

  const handleConfirm = async () => {
    setLoading(true);

    try {
      // Upload file if present
      let attachmentUrl = null;
      if (fileList.length > 0) {
        const uploadResult = await uploadFile(fileList[0].originFileObj);
        attachmentUrl = uploadResult.url;
      }

      // Create leave request with attachment URL
      await onSubmit({ ...confirmData, attachment_url: attachmentUrl });

      setLoading(false);
      setSuccess(true);

      setTimeout(() => {
        setSuccess(false);
        setStep(0);
        setConfirmData(null);
        setFileList([]);
        form.resetFields();
        onCancel();
      }, 3000);
    } catch (error) {
      setLoading(false);
      let errorMsg = "Failed to submit leave request";
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      message.error(errorMsg);
    }
  };

  return (
    <Modal
      open={open}
      onCancel={success ? null : onCancel}
      footer={null}
      width={720}
      destroyOnHidden
    >
      {!success && (
        <>
          <Title level={4}>New Leave Request</Title>
          <Steps
            current={step}
            items={[{ title: "Fill" }, { title: "Confirm" }]}
          />

          {step === 0 && (
            <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
              {/* 1. Leave Category — always available */}
              <Form.Item
                name="leaveCategory"
                label="Leave Category"
                rules={[{ required: true, message: "Please select leave category" }]}
              >
                <Select
                  size="large"
                  placeholder="Select leave category"
                  options={categories.map((category) => ({
                    value: category.id,
                    label: category.name,
                  }))}
                />
              </Form.Item>

              {/* 2. Date — unlocked once a category is chosen */}
              <Form.Item
                name="date"
                label="Date"
                rules={[{ required: true }]}
                tooltip={!categoryChosen ? "Select a leave category first" : undefined}
              >
                <RangePicker
                  size="large"
                  style={{ width: "100%" }}
                  allowEmpty={[true, true]}
                  disabled={!categoryChosen}
                  disabledDate={disabledDate}
                />
              </Form.Item>

              {/* 3. Duration / Time — unlocked once a same-day date is chosen */}
              {sameDay && (
                <Form.Item name="dayType" label="Duration" initialValue="full">
                  <Radio.Group buttonStyle="solid" size="large">
                    <Radio.Button value="full">Full Day</Radio.Button>
                    <Radio.Button value="custom">Custom Hour</Radio.Button>
                  </Radio.Group>
                </Form.Item>
              )}

              {sameDay && dayType === "custom" && (
                <>
                  <Space>
                    <Form.Item name="startTime" label="Start Time" rules={[{ required: true }]}>
                      <HourSelect aria-label="Start time" />
                    </Form.Item>
                    <Form.Item name="endTime" label="End Time" rules={[{ required: true }]}>
                      <HourSelect aria-label="End time" />
                    </Form.Item>
                  </Space>

                  {previewHours > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text>
                        Estimated:{" "}
                        <Text strong>{previewHours.toFixed(1)}h</Text>
                        {values?.startTime &&
                          values?.endTime &&
                          values.endTime.hour() < values.startTime.hour() && (
                            <Text type="secondary"> · ends next day</Text>
                          )}
                      </Text>

                      {previewHours > 8 && (
                        <div>
                          <Text type="danger">
                            ⚠ Custom hours cannot exceed 8 hours per day
                          </Text>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* 4. Reason & Attachment — unlocked once a date is chosen */}
              <Form.Item
                name="reason"
                label="Reason"
                rules={[{ required: true }]}
                tooltip={!dateChosen ? "Select a date first" : undefined}
              >
                <TextArea rows={3} disabled={!dateChosen} />
              </Form.Item>

              <Form.Item label="Attachment">
                <Upload
                  beforeUpload={() => false}
                  fileList={fileList}
                  onChange={({ fileList }) => setFileList(fileList)}
                  accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                  maxCount={1}
                  disabled={!dateChosen}
                >
                  <Button icon={<UploadOutlined />} disabled={!dateChosen}>
                    Upload
                  </Button>
                </Upload>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  PDF or images only, max 5MB
                </Text>
              </Form.Item>

              <Button
                type="primary"
                block
                size="large"
                icon={<ArrowRightOutlined />}
                onClick={handleContinue}
              >
                Continue
              </Button>
            </Form>
          )}

          {step === 1 && confirmData && (
            <>
              <Card
                style={{
                  marginTop: 24,
                  borderRadius: 16,
                  background: "var(--color-surface-muted)",
                }}
              >
                <Title level={5}>Information Confirm</Title>
                <Text type="secondary">
                  Please review carefully before submitting
                </Text>

                <Divider />

                <Space
                  direction="vertical"
                  size="middle"
                  style={{ width: "100%" }}
                >
                  {/* LEAVE CATEGORY */}
                  <div
                    style={{ display: "flex", justifyContent: "space-between" }}
                  >
                    <Text type="secondary">Leave Category</Text>
                    <Tag
                      style={{
                        color: confirmData.balanceBucket === "VACATION" ? "var(--color-accent)" : "var(--color-danger)",
                        background: confirmData.balanceBucket === "VACATION" ? "var(--color-accent-soft)" : "var(--color-danger-soft)",
                        border: "1px solid currentColor",
                      }}
                    >
                      {confirmData.categoryName}
                    </Tag>
                  </div>

                  {/* DATE */}
                  <div
                    style={{ display: "flex", justifyContent: "space-between" }}
                  >
                    <Text type="secondary">Date</Text>
                    <Text strong>
                      {confirmData.date[0].format("YYYY-MM-DD")} →{" "}
                      {confirmData.date[1].format("YYYY-MM-DD")}
                    </Text>
                  </div>

                  {/* DAY TYPE */}
                  {sameDay && (
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                      }}
                    >
                      <Text type="secondary">Day Type</Text>
                      <Text strong>
                        {confirmData.dayType === "custom"
                          ? "Custom Hour"
                          : "Full Day"}
                      </Text>
                    </div>
                  )}

                  {sameDay && confirmData.dayType === "custom" && (
                    <>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <Text type="secondary">Work shift date</Text>
                        <Text strong>{confirmData.date[0].format("YYYY-MM-DD")}</Text>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                        <Text type="secondary">Actual leave date</Text>
                        <Text strong>
                          {confirmData.date[0].add(confirmData.startDayOffset, "day").format("YYYY-MM-DD")}
                        </Text>
                      </div>
                    </>
                  )}

                  {/* TIME */}
                  {sameDay && confirmData.dayType === "custom" && (
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                      }}
                    >
                      <Text type="secondary">Time</Text>
                      <Text strong>
                        {confirmData.startTime.format("hh:mm A")} →{" "}
                        {confirmData.endTime.format("hh:mm A")}
                        {confirmData.endTime.hour() < confirmData.startTime.hour()
                          ? " (next day)"
                          : ""}
                      </Text>
                    </div>
                  )}

                  {/* DEDUCT HIGHLIGHT — only for balance-affecting categories;
                      NONE-bucket leave is settled by HR/Finance at payslip time */}
                  {confirmData.balanceBucket !== "NONE" && (
                    <div
                      style={{
                        padding: 16,
                        borderRadius: 12,
                        background:
                          confirmData.totalHours > (confirmData.remainingHours || 0)
                            ? "var(--color-danger-soft)"
                            : "var(--color-accent-soft)",
                        border:
                          confirmData.totalHours > (confirmData.remainingHours || 0)
                            ? "1px solid var(--color-danger)"
                            : "1px solid var(--color-border-strong)",
                      }}
                    >
                      <Text
                        strong
                        style={{
                          color:
                            confirmData.totalHours > (confirmData.remainingHours || 0)
                              ? "var(--color-danger)"
                              : "var(--color-accent)",
                          fontSize: 16,
                        }}
                      >
                        {`Your leave balance will be deducted by ${confirmData.totalHours.toFixed(1)} hours`}
                      </Text>

                      {confirmData.totalHours > (confirmData.remainingHours || 0) && (
                        <div style={{ marginTop: 8 }}>
                          <Text type="danger">
                            ⚠ Your current balance is only {confirmData.remainingHours?.toFixed(1) || 0}h
                          </Text>
                        </div>
                      )}
                    </div>
                  )}

                  {/* REASON */}
                  <div>
                    <Text type="secondary">Reason</Text>
                    <div
                      style={{
                        marginTop: 8,
                        padding: 12,
                        borderRadius: 8,
                        background: "var(--color-surface-muted)",
                        border: "1px solid var(--color-border-strong)",
                      }}
                    >
                      {confirmData.reason}
                    </div>
                  </div>

                  {/* ATTACHMENT */}
                  {fileList.length > 0 && (
                    <div>
                      <Text type="secondary">Attachment</Text>
                      <div style={{ marginTop: 8 }}>
                        {fileList.map((f) => (
                          <Tag
                            key={f.uid}
                            style={{
                              color: "var(--color-accent)",
                              background: "var(--color-accent-soft)",
                              border: "1px solid var(--color-accent)",
                            }}
                          >
                            {f.name}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  )}
                </Space>
              </Card>

              <Divider />

              {/* ACTIONS */}
              <Space style={{ width: "100%", justifyContent: "space-between" }}>
                <Button size="large" onClick={() => setStep(0)}>
                  Back
                </Button>

                <Button
                  type="primary"
                  size="large"
                  icon={<CheckCircleOutlined />}
                  loading={loading}
                  onClick={handleConfirm}
                  className="app-button-primary"
                  style={{
                    borderRadius: 10,
                    paddingInline: 32,
                  }}
                >
                  Confirm Request
                </Button>
              </Space>
            </>
          )}
        </>
      )}

      {success && (
        <Result
          status="success"
          title="Leave request submitted"
          subTitle="This window will close automatically"
        />
      )}
    </Modal>
  );
}
