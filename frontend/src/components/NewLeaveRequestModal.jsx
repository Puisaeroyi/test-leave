import { useState, useEffect } from "react";
import {
  Modal,
  Steps,
  Typography,
  Form,
  Select,
  DatePicker,
  Radio,
  TimePicker,
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

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

export default function NewLeaveRequestModal({
  open,
  onCancel,
  onSubmit,
  balances = [], // Array of 4 balances
  initialDate = null, // Pre-selected date from calendar click
}) {
  const [step, setStep] = useState(0);
  const [form] = Form.useForm();
  const [confirmData, setConfirmData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(false);

  // Pre-fill date from calendar click
  useEffect(() => {
    if (open && initialDate) {
      form.setFieldsValue({ date: [initialDate, initialDate] });
    }
  }, [open, initialDate, form]);

  // Fetch leave categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setCategoriesLoading(true);
        const data = await getLeaveCategories();
        setCategories(data);
      } catch (error) {
        console.error("Failed to fetch categories:", error);
        message.error("Failed to load leave categories");
      } finally {
        setCategoriesLoading(false);
      }
    };
    fetchCategories();
  }, []);

  const values = Form.useWatch([], form);
  const leaveCategory = Form.useWatch("leaveCategory", form);
  const sameDay = values?.date && values.date[0]?.isSame(values.date[1], "day");
  const dayType = values?.dayType || "full";

  // Different date rules: Sick leave allows up to 2 weeks retroactive, Vacation requires 3-day advance
  const minLeaveDate =
    leaveCategory === "sick"
      ? dayjs().subtract(14, "day").startOf("day")  // Allow 2 weeks retroactive for sick leave
      : dayjs().add(3, "day").startOf("day");

  const disabledDate = (current) => {
    if (!leaveCategory) return false;
    return current && current < minLeaveDate;
  };

  const calculateHours = (start, end) => {
    if (!start || !end) return 0;
    return end.diff(start, "minute") / 60;
  };

  // Calculate working days (Mon-Fri only, excludes weekends)
  const countWorkingDays = (startDate, endDate) => {
    if (!startDate || !endDate) return 0;
    let count = 0;
    let current = startDate.startOf("day");
    const end = endDate.startOf("day");

    while (current.isBefore(end) || current.isSame(end, "day")) {
      const dayOfWeek = current.day(); // 0=Sunday, 6=Saturday
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
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

  // Get balance type key based on leaveCategory and exemptType
  const getBalanceKey = (category, exemptType) =>
    category === "vacation"
      ? exemptType === "exempt"
        ? "EXEMPT_VACATION"
        : "NON_EXEMPT_VACATION"
      : exemptType === "exempt"
      ? "EXEMPT_SICK"
      : "NON_EXEMPT_SICK";

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
          content: "End time must be after start time.",
        });
        return;
      }
    } else {
      // Count only working days (Mon-Fri), exclude weekends
      const workingDays = countWorkingDays(data.date[0], data.date[1]);
      hours = workingDays * 8;
    }

    // Find the specific balance based on category and exempt type
    const balanceKey = getBalanceKey(data.leaveCategory, data.exemptType);
    const selectedBalance = balances.find(b => b.type === balanceKey);

    setConfirmData({
      ...data,
      totalHours: hours,
      remainingHours: selectedBalance?.remaining_hours || 0,
      allocated_hours: selectedBalance?.allocated_hours || 0,
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
      destroyOnClose
    >
      {!success && (
        <>
          <Title level={4}>New Leave Request</Title>
          <Steps
            current={step}
            items={[{ title: "Fill" }, { title: "Confirm" }]}
          />

          {step === 0 && (
            <Form
              form={form}
              layout="vertical"
              style={{ marginTop: 24 }}
              placeholder="Select leave type"
            >
              <Form.Item
                name="leaveCategory"
                label="Leave Category"
                rules={[{ required: true, message: "Please select leave category" }]}
              >
                <Select
                  size="large"
                  placeholder="Select leave category"
                  options={[
                    { value: "vacation", label: "Vacation" },
                    { value: "sick", label: "Sick Leave" },
                  ]}
                />
              </Form.Item>

              {leaveCategory && (
                <Form.Item
                  name="exemptType"
                  label="Leave Type"
                  rules={[{ required: true, message: "Please select leave type" }]}
                  initialValue="exempt"
                >
                  <Radio.Group buttonStyle="solid" size="large">
                    <Radio.Button value="exempt">Exempt</Radio.Button>
                    <Radio.Button value="non-exempt">Non-Exempt</Radio.Button>
                  </Radio.Group>
                </Form.Item>
              )}

              <Form.Item name="date" label="Date" rules={[{ required: true }]}>
                <RangePicker
                  size="large"
                  style={{ width: "100%" }}
                  disabledDate={disabledDate}
                />
              </Form.Item>

              {sameDay && (
                <Form.Item name="dayType" initialValue="full">
                  <Radio.Group buttonStyle="solid" size="large">
                    <Radio.Button value="full">Full Day</Radio.Button>
                    <Radio.Button value="custom">Custom Hour</Radio.Button>
                  </Radio.Group>
                </Form.Item>
              )}

              {sameDay && dayType === "custom" && (
                <>
                  <Space>
                    <Form.Item name="startTime" rules={[{ required: true }]}>
                      <TimePicker format="HH:mm" minuteStep={30} showNow={false} />
                    </Form.Item>
                    <Form.Item name="endTime" rules={[{ required: true }]}>
                      <TimePicker format="HH:mm" minuteStep={30} showNow={false} />
                    </Form.Item>
                  </Space>

                  {previewHours > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text>
                        Estimated:{" "}
                        <Text strong>{previewHours.toFixed(1)}h</Text>
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

              <Form.Item
                name="reason"
                label="Reason"
                rules={[{ required: true }]}
              >
                <TextArea rows={3} />
              </Form.Item>

              <Form.Item label="Attachment">
                <Upload
                  beforeUpload={() => false}
                  fileList={fileList}
                  onChange={({ fileList }) => setFileList(fileList)}
                  accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                  maxCount={1}
                >
                  <Button icon={<UploadOutlined />}>Upload</Button>
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
                  background: "#fafafa",
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
                    <Tag color={confirmData.leaveCategory === "vacation" ? "blue" : "red"}>
                      {confirmData.leaveCategory === "vacation" ? "Vacation" : "Sick Leave"}
                    </Tag>
                  </div>

                  {/* LEAVE TYPE */}
                  <div
                    style={{ display: "flex", justifyContent: "space-between" }}
                  >
                    <Text type="secondary">Leave Type</Text>
                    <Tag color="geekblue">
                      {confirmData.exemptType === "exempt" ? "Exempt" : "Non-Exempt"}
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
                        {confirmData.startTime.format("HH:mm")} →{" "}
                        {confirmData.endTime.format("HH:mm")}
                      </Text>
                    </div>
                  )}

                  {/* DEDUCT HIGHLIGHT */}
                  <div
                    style={{
                      padding: 16,
                      borderRadius: 12,
                      background:
                        confirmData.totalHours > (confirmData.remainingHours || 0)
                          ? "rgba(255,77,79,0.12)"
                          : "rgba(22,119,255,0.12)",
                      border:
                        confirmData.totalHours > (confirmData.remainingHours || 0)
                          ? "1px solid #ff4d4f"
                          : "1px solid #91caff",
                    }}
                  >
                    <Text
                      strong
                      style={{
                        color:
                          confirmData.totalHours > (confirmData.remainingHours || 0)
                            ? "#ff4d4f"
                            : "#1677ff",
                        fontSize: 16,
                      }}
                    >
                      Your leave balance will be deducted by{" "}
                      {confirmData.totalHours.toFixed(1)} hours
                    </Text>

                    {confirmData.totalHours > (confirmData.remainingHours || 0) && (
                      <div style={{ marginTop: 8 }}>
                        <Text type="danger">
                          ⚠ Your current balance is only {confirmData.remainingHours?.toFixed(1) || 0}h
                        </Text>
                      </div>
                    )}
                  </div>

                  {/* REASON */}
                  <div>
                    <Text type="secondary">Reason</Text>
                    <div
                      style={{
                        marginTop: 8,
                        padding: 12,
                        borderRadius: 8,
                        background: "#fff",
                        border: "1px solid #f0f0f0",
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
                          <Tag key={f.uid} color="processing">
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
                  style={{
                    borderRadius: 10,
                    paddingInline: 32,
                    background: "linear-gradient(135deg, #1677ff, #4096ff)",
                    border: "none",
                    boxShadow: "0 6px 16px rgba(22,119,255,0.3)",
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
