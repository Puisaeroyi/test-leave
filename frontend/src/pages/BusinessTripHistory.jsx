import { useState, useEffect } from "react";
import {
  Table,
  Tag,
  Button,
  Modal,
  Descriptions,
  Typography,
  Space,
  message,
} from "antd";
import { EyeOutlined, PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getBusinessTrips, cancelBusinessTrip } from "@api/businessTripApi";
import NewBusinessTripModal from "@components/NewBusinessTripModal";

const { Title } = Typography;

export default function BusinessTripHistory() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [openNew, setOpenNew] = useState(false);

  // Fetch business trips on mount
  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      setLoading(true);
      const response = await getBusinessTrips();
      setData(response.results || []);
    } catch (error) {
      console.error("Failed to fetch business trips:", error);
      message.error(error.response?.data?.error || "Failed to load business trips");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    // Modal handles API call, just refresh list
    await fetchTrips();
  };

  const handleCancel = async (id) => {
    try {
      await cancelBusinessTrip(id);
      message.success("Business trip cancelled");
      setSelected(null);
      fetchTrips(); // Refresh list
    } catch (error) {
      console.error("Failed to cancel business trip:", error);
      message.error(error.response?.data?.error || "Failed to cancel business trip");
    }
  };

  const columns = [
    {
      title: "Destination",
      render: (_, r) => <Tag color="geekblue">{r.city}, {r.country}</Tag>,
    },
    {
      title: "Date",
      render: (_, r) =>
        `${dayjs(r.start_date).format("DD/MM/YYYY")} → ${dayjs(r.end_date).format(
          "DD/MM/YYYY"
        )}`,
    },
    {
      title: "Action",
      render: (_, r) => (
        <Button icon={<EyeOutlined />} onClick={() => setSelected(r)}>
          View Detail
        </Button>
      ),
    },
  ];

  return (
    <>
      <Space
        style={{ width: "100%", justifyContent: "space-between" }}
      >
        <Title level={4}>Business Trip History</Title>

        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setOpenNew(true)}
        >
          New Business Trip
        </Button>
      </Space>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={false}
      />

      {/* DETAIL MODAL */}
      <Modal
        open={!!selected}
        onCancel={() => setSelected(null)}
        footer={null}
        title="Business Trip Detail"
      >
        {selected && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="City">
              {selected.city}
            </Descriptions.Item>

            <Descriptions.Item label="Country">
              {selected.country}
            </Descriptions.Item>

            <Descriptions.Item label="Date">
              {dayjs(selected.start_date).format("DD/MM/YYYY")} →{" "}
              {dayjs(selected.end_date).format("DD/MM/YYYY")}
            </Descriptions.Item>

            <Descriptions.Item label="Note">
              {selected.note || "-"}
            </Descriptions.Item>

            {selected.attachment_url && (
              <Descriptions.Item label="Attachment">
                <a href={selected.attachment_url} target="_blank" rel="noopener noreferrer">
                  View Attachment
                </a>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* NEW BUSINESS TRIP */}
      <NewBusinessTripModal
        open={openNew}
        onCancel={() => setOpenNew(false)}
        onSubmit={handleCreate}
      />
    </>
  );
}
