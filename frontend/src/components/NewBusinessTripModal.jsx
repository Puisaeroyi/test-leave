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
import { createBusinessTrip } from "@api/businessTripApi";
import { uploadFile } from "@api/dashboardApi";

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

export default function NewBusinessTripModal({ open, onCancel, onSubmit, initialDate = null }) {
  const [form] = Form.useForm();
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState([]);

  // Pre-fill date from calendar click
  useEffect(() => {
    if (open && initialDate) {
      form.setFieldsValue({ date: [initialDate, initialDate] });
    }
  }, [open, initialDate, form]);

  const disabledDate = (current) => {
    return current && current < dayjs().startOf("day");
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      // Upload file if present
      let attachmentUrl = "";
      if (fileList.length > 0) {
        const uploadResult = await uploadFile(fileList[0].originFileObj);
        attachmentUrl = uploadResult.url;
      }

      // Call API to create business trip
      await createBusinessTrip({
        city: values.city,
        country: values.country,
        date: values.date,
        note: values.note || "",
        attachment_url: attachmentUrl,
      });

      setLoading(false);
      setSuccess(true);
      onSubmit(values);

      setTimeout(() => {
        setSuccess(false);
        form.resetFields();
        setFileList([]);
        onCancel();
      }, 2000);
    } catch (error) {
      console.error("Failed to create business trip:", error);
      setLoading(false);
      message.error(error.response?.data?.error || "Failed to create business trip");
    }
  };

  return (
    <Modal
      open={open}
      onCancel={success ? null : onCancel}
      footer={null}
      destroyOnClose
      width={600}
    >
      {!success && (
        <>
          <Title level={4}>New Business Trip</Title>
          <Text type="secondary">
            Please provide your business trip information
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
              <Upload
                beforeUpload={() => false}
                fileList={fileList}
                onChange={({ fileList }) => setFileList(fileList)}
                accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                maxCount={1}
              >
                <Button icon={<UploadOutlined />}>Upload file</Button>
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
              Submit Business Trip
            </Button>
          </Form>
        </>
      )}

      {success && (
        <Result
          status="success"
          title="Business trip submitted"
          subTitle="Your trip has been saved successfully."
        />
      )}
    </Modal>
  );
}
