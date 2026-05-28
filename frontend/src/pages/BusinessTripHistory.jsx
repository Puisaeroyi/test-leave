import { useState, useEffect, useCallback } from "react";
import {
  Card,
  Table,
  Tag,
  Button,
  Modal,
  Descriptions,
  Space,
  message,
} from "antd";
import { EyeOutlined, PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getBusinessTrips } from "@api/businessTripApi";
import { getMediaUrl } from "@api/http";
import NewBusinessTripModal from "@components/NewBusinessTripModal";

export default function BusinessTripHistory() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [openNew, setOpenNew] = useState(false);

  const fetchTrips = useCallback(async () => {
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
  }, []);

  // Fetch business trips on mount
  useEffect(() => {
    fetchTrips();
  }, [fetchTrips]);

  const handleCreate = async () => {
    // Modal handles API call, just refresh list
    await fetchTrips();
  };

  const columns = [
    {
      title: "Destination",
      render: (_, r) => <Tag style={{ color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }}>{r.city}, {r.country}</Tag>,
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
    <div className="page-shell">
      <section className="page-toolbar">
        <div>
          <div className="page-kicker">My Travel Plans</div>
          <h1 className="page-title">Business Trip History</h1>
          <p className="page-subtitle">
            Keep business trip dates, destinations, attachments, and changes in one place.
          </p>
        </div>

        <Button
          type="primary"
          className="app-button-primary"
          icon={<PlusOutlined />}
          onClick={() => setOpenNew(true)}
        >
          New Business Trip
        </Button>
      </section>

      <Card className="page-panel table-card">
        <Table
          rowKey="id"
          columns={columns}
          dataSource={data}
          loading={loading}
          pagination={false}
          scroll={{ x: 600 }}
        />
      </Card>

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
                <a href={getMediaUrl(selected.attachment_url)} target="_blank" rel="noopener noreferrer">
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
    </div>
  );
}
