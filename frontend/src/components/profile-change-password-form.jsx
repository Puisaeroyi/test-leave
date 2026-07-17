import { useState } from "react";
import { Form, Input, Button, Modal, App } from "antd";
import { LockOutlined } from "@ant-design/icons";
import { changeMyPassword } from "@api/authApi";
import { useAuth } from "@auth/authContext";

/**
 * Secondary security action: opens a modal so Profile details stay primary
 * and fully visible without competing vertical space.
 * On success swaps JWT pair so this session continues (other devices signed out).
 */
export default function ProfileChangePasswordForm({ buttonProps = {} }) {
  const { message } = App.useApp();
  const { updateUser } = useAuth();
  const [form] = Form.useForm();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const close = () => {
    setOpen(false);
    form.resetFields();
  };

  const onFinish = async (values) => {
    try {
      setLoading(true);
      const updatedUser = await changeMyPassword({
        currentPassword: values.currentPassword,
        newPassword: values.newPassword,
        newPasswordConfirm: values.newPasswordConfirm,
      });
      if (updatedUser) {
        updateUser(updatedUser);
      }
      form.resetFields();
      setOpen(false);
      message.success("Password changed. Other devices have been signed out.");
    } catch (err) {
      const data = err.response?.data || {};
      const fieldMap = {
        current_password: "currentPassword",
        new_password: "newPassword",
        new_password_confirm: "newPasswordConfirm",
      };
      const fields = Object.entries(fieldMap)
        .filter(([apiKey]) => data[apiKey])
        .map(([apiKey, formName]) => ({
          name: formName,
          errors: Array.isArray(data[apiKey]) ? data[apiKey] : [String(data[apiKey])],
        }));

      if (fields.length) {
        form.setFields(fields);
      } else {
        message.error(
          data.error ||
            data.detail ||
            data.non_field_errors?.[0] ||
            "Failed to change password"
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        icon={<LockOutlined />}
        onClick={() => setOpen(true)}
        {...buttonProps}
      >
        Change password
      </Button>

      <Modal
        title="Change password"
        open={open}
        onCancel={close}
        footer={null}
        destroyOnHidden
        width={440}
        centered
      >
        <p style={{ marginTop: 0, marginBottom: 16, color: "var(--color-muted)" }}>
          You will stay signed in on this device. Other sessions will be signed out.
        </p>

        <Form form={form} layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            name="currentPassword"
            label="Current Password"
            rules={[{ required: true, message: "Please enter your current password" }]}
          >
            <Input.Password placeholder="Current password" autoComplete="current-password" />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="New Password"
            rules={[
              { required: true, message: "Please enter a new password" },
              { min: 8, message: "Password must be at least 8 characters" },
            ]}
          >
            <Input.Password placeholder="New password" autoComplete="new-password" />
          </Form.Item>

          <Form.Item
            name="newPasswordConfirm"
            label="Confirm New Password"
            dependencies={["newPassword"]}
            rules={[
              { required: true, message: "Please confirm your new password" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("newPassword") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("Passwords do not match"));
                },
              }),
            ]}
          >
            <Input.Password placeholder="Confirm new password" autoComplete="new-password" />
          </Form.Item>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
            <Button onClick={close} disabled={loading}>
              Cancel
            </Button>
            <Button
              type="primary"
              className="app-button-primary"
              htmlType="submit"
              loading={loading}
            >
              Update password
            </Button>
          </div>
        </Form>
      </Modal>
    </>
  );
}
