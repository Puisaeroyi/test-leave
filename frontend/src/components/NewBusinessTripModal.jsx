import { useState, useEffect } from "react";
import {
  Modal,
  Form,
  Input,
  DatePicker,
  Upload,
  Button,
  Typography,
  Result,
  message,
} from "antd";
import { UploadOutlined, CheckCircleOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { createBusinessTrip, updateBusinessTrip } from "@api/businessTripApi";
import { uploadFile } from "@api/dashboardApi";

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

export default function NewBusinessTripModal({
  open,
  onCancel,
  onSubmit,
  initialDate = null,
  mode = "create",
  initialRecord = null,
}) {
  const isEdit = mode === "edit" && !!initialRecord;
  const [form] = Form.useForm();
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [removeAttachment, setRemoveAttachment] = useState(false);
  const [existingAttachment, setExistingAttachment] = useState(null);

  useEffect(() => {
    if (open && initialDate && !isEdit) {
      form.setFieldsValue({ date: [initialDate, initialDate] });
    }
  }, [open, initialDate, form, isEdit]);

  useEffect(() => {
    if (!open || !isEdit || !initialRecord) return;
    form.setFieldsValue({
      city: initialRecord.city,
      country: initialRecord.country,
      date: [dayjs(initialRecord.start_date), dayjs(initialRecord.end_date)],
      note: initialRecord.note || "",
    });
    setExistingAttachment(initialRecord.attachment_url || null);
    setRemoveAttachment(false);
    setFileList([]);
    setSuccess(false);
  }, [open, isEdit, initialRecord, form]);

  const disabledDate = (current) => {
    return current && current < dayjs().startOf("day");
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      let attachmentPayload = {};
      if (fileList.length > 0) {
        const uploadResult = await uploadFile(fileList[0].originFileObj);
        attachmentPayload = { attachment_url: uploadResult.url };
      } else if (isEdit && removeAttachment) {
        attachmentPayload = { attachment_url: "" };
      } else if (!isEdit) {
        attachmentPayload = { attachment_url: "" };
      }

      if (isEdit) {
        await updateBusinessTrip(initialRecord.id, {
          city: values.city,
          country: values.country,
          date: values.date,
          note: values.note || "",
          expectedUpdatedAt: initialRecord.updated_at,
          ...attachmentPayload,
        });
      } else {
        await createBusinessTrip({
          city: values.city,
          country: values.country,
          date: values.date,
          note: values.note || "",
          ...attachmentPayload,
        });
      }

      setLoading(false);
      setSuccess(true);
      onSubmit?.(values);

      setTimeout(() => {
        setSuccess(false);
        form.resetFields();
        setFileList([]);
        setRemoveAttachment(false);
        setExistingAttachment(null);
        onCancel();
      }, 1500);
    } catch (error) {
      console.error("Failed to save business trip:", error);
      setLoading(false);
      if (error.response?.status === 409) {
        message.warning(
          error.response?.data?.error
          || "This trip was updated elsewhere. Please refresh.",
        );
        return;
      }
      message.error(
        error.response?.data?.error
        || (isEdit ? "Failed to update business trip" : "Failed to create business trip"),
      );
    }
  };

  return (
    <Modal
      open={open}
      onCancel={success ? null : onCancel}
      footer={null}
      destroyOnHidden
      width={600}
    >
      {!success && (
        <>
          <Title level={4}>{isEdit ? "Edit Business Trip" : "New Business Trip"}</Title>
          <Text type="secondary">
            {isEdit
              ? "Update your trip details before the start date."
              : "Please provide your business trip information"}
          </Text>

          <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
            <Form.Item
              name="city"
              label="City"
              rules={[{ required: true, message: "Please enter city" }]}
            >
              <Input size="large" placeholder="Ex: Singapore" />
            </Form.Item>

            <Form.Item
              name="country"
              label="Country"
              rules={[{ required: true, message: "Please enter country" }]}
            >
              <Input size="large" placeholder="Ex: Singapore" />
            </Form.Item>

            <Form.Item
              name="date"
              label="Date From - To"
              rules={[{ required: true, message: "Please select date range" }]}
            >
              <RangePicker
                size="large"
                style={{ width: "100%" }}
                disabledDate={disabledDate}
              />
            </Form.Item>

            <Form.Item name="note" label="Note">
              <TextArea rows={3} placeholder="Additional notes (optional)" />
            </Form.Item>

            <Form.Item label="Attachment">
              {isEdit && existingAttachment && !removeAttachment && fileList.length === 0 && (
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">Current attachment kept. </Text>
                  <Button type="link" size="small" danger onClick={() => setRemoveAttachment(true)}>
                    Remove
                  </Button>
                </div>
              )}
              {isEdit && removeAttachment && fileList.length === 0 && (
                <div style={{ marginBottom: 8 }}>
                  <Text type="warning">Attachment will be removed. </Text>
                  <Button type="link" size="small" onClick={() => setRemoveAttachment(false)}>
                    Undo
                  </Button>
                </div>
              )}
              <Upload
                beforeUpload={() => false}
                fileList={fileList}
                onChange={({ fileList: next }) => {
                  setFileList(next);
                  if (next.length > 0) setRemoveAttachment(false);
                }}
                accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                maxCount={1}
              >
                <Button icon={<UploadOutlined />}>
                  {isEdit ? "Replace file" : "Upload file"}
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
              icon={<CheckCircleOutlined />}
              loading={loading}
              onClick={handleSubmit}
            >
              {isEdit ? "Save Changes" : "Submit Business Trip"}
            </Button>
          </Form>
        </>
      )}

      {success && (
        <Result
          status="success"
          title={isEdit ? "Business trip updated" : "Business trip submitted"}
          subTitle={
            isEdit
              ? "Your changes have been saved."
              : "Your trip has been saved successfully."
          }
        />
      )}
    </Modal>
  );
}
