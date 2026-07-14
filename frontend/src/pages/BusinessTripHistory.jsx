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
  Typography,
} from "antd";
import { EyeOutlined, PlusOutlined, EditOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getBusinessTrips } from "@api/businessTripApi";
import { getMediaUrl } from "@api/http";
import NewBusinessTripModal from "@components/NewBusinessTripModal";
import ResponsiveRecordCard, { ResponsiveRecordRow } from "@components/ResponsiveRecordCard";

const { Text } = Typography;

export default function BusinessTripHistory() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [openNew, setOpenNew] = useState(false);
  const [editRecord, setEditRecord] = useState(null);

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

  useEffect(() => {
    fetchTrips();
  }, [fetchTrips]);

  const handleCreate = async () => {
    await fetchTrips();
  };

  const openEdit = (trip) => {
    setSelected(null);
    setEditRecord(trip);
    setOpenNew(true);
  };

  const columns = [
    {
      title: "Destination",
      render: (_, r) => (
        <Tag style={{ color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }}>
          {r.city}, {r.country}
        </Tag>
      ),
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
        <Space>
          <Button icon={<EyeOutlined />} onClick={() => setSelected(r)}>
            View Detail
          </Button>
          {r.can_edit && (
            <Button icon={<EditOutlined />} onClick={() => openEdit(r)}>
              Edit
            </Button>
          )}
        </Space>
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
          onClick={() => {
            setEditRecord(null);
            setOpenNew(true);
          }}
        >
          New Business Trip
        </Button>
      </section>

      <Card className="page-panel table-card">
        <div className="responsive-desktop-table">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={data}
            loading={loading}
            pagination={false}
            scroll={{ x: 600 }}
          />
        </div>
        <div className="responsive-mobile-list">
          <div className="responsive-record-list" aria-live="polite">
            {data.map((trip) => (
              <ResponsiveRecordCard
                key={trip.id}
                title={`${trip.city}, ${trip.country}`}
                onClick={() => setSelected(trip)}
                ariaLabel={`View business trip to ${trip.city}, ${trip.country}`}
                footer={
                  <Space>
                    <Button icon={<EyeOutlined />} onClick={() => setSelected(trip)}>
                      View Detail
                    </Button>
                    {trip.can_edit && (
                      <Button icon={<EditOutlined />} onClick={() => openEdit(trip)}>
                        Edit
                      </Button>
                    )}
                  </Space>
                }
              >
                <ResponsiveRecordRow label="Start">
                  {dayjs(trip.start_date).format("DD/MM/YYYY")}
                </ResponsiveRecordRow>
                <ResponsiveRecordRow label="End">
                  {dayjs(trip.end_date).format("DD/MM/YYYY")}
                </ResponsiveRecordRow>
                <ResponsiveRecordRow label="Attachment">
                  {trip.attachment_url ? "Available" : "None"}
                </ResponsiveRecordRow>
              </ResponsiveRecordCard>
            ))}
            {!loading && data.length === 0 && (
              <div className="responsive-empty-state">No business trips found.</div>
            )}
          </div>
        </div>
      </Card>

      <Modal
        open={!!selected}
        onCancel={() => setSelected(null)}
        footer={
          selected?.can_edit
            ? [
                <Button key="edit" type="primary" icon={<EditOutlined />} onClick={() => openEdit(selected)}>
                  Edit trip
                </Button>,
              ]
            : null
        }
        title="Business Trip Detail"
      >
        {selected && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="City">{selected.city}</Descriptions.Item>
            <Descriptions.Item label="Country">{selected.country}</Descriptions.Item>
            <Descriptions.Item label="Date">
              {dayjs(selected.start_date).format("DD/MM/YYYY")} →{" "}
              {dayjs(selected.end_date).format("DD/MM/YYYY")}
            </Descriptions.Item>
            <Descriptions.Item label="Note">{selected.note || "-"}</Descriptions.Item>
            {!selected.can_edit && (
              <Descriptions.Item label="Editing">
                <Text type="secondary">
                  Editing is locked once the trip start date has been reached in your location timezone.
                </Text>
              </Descriptions.Item>
            )}
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

      <NewBusinessTripModal
        open={openNew}
        onCancel={() => {
          setOpenNew(false);
          setEditRecord(null);
        }}
        onSubmit={handleCreate}
        mode={editRecord ? "edit" : "create"}
        initialRecord={editRecord}
      />
    </div>
  );
}
