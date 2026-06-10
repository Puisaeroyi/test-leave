import { useState, useEffect, useCallback } from "react";
import {
  Card,
  Table,
  Tag,
  Button,
  Modal,
  Descriptions,
  Typography,
  Space,
  message,
} from "antd";
import { EyeOutlined, ReloadOutlined, PaperClipOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getTeamBusinessTrips } from "@api/businessTripApi";
import { getMediaUrl } from "@api/http";
import ResponsiveRecordCard, { ResponsiveRecordRow } from "@components/ResponsiveRecordCard";

const { Text } = Typography;

export default function BusinessTripTickets() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  const fetchTrips = useCallback(async (page = 1, pageSize = 10) => {
    try {
      setLoading(true);
      const response = await getTeamBusinessTrips({ page, page_size: pageSize });
      setData(response.results || []);
      setPagination(prev => ({ ...prev, current: page, pageSize, total: response.count || 0 }));
    } catch (error) {
      console.error("Failed to fetch team business trips:", error);
      message.error(error.response?.data?.error || "Failed to load team business trips");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch team business trips on mount
  useEffect(() => {
    fetchTrips();
  }, [fetchTrips]);

  const columns = [
    {
      title: "Employee Name",
      dataIndex: "user_name",
      align: "center",
      render: (v) => <Text strong>{v}</Text>,
    },
    {
      title: "Destination",
      render: (_, r) => <Tag style={{ color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }}>{r.city}, {r.country}</Tag>,
    },
    {
      title: "Date Range",
      render: (_, r) =>
        `${dayjs(r.start_date).format("DD/MM/YYYY")} → ${dayjs(r.end_date).format(
          "DD/MM/YYYY"
        )}`,
    },
    {
      title: "Action",
      align: "center",
      render: (_, r) => (
        <Button
          type="primary"
          ghost
          icon={<EyeOutlined />}
          onClick={() => setSelected(r)}
        >
          View Detail
        </Button>
      ),
    },
  ];

  return (
    <div className="page-shell">
      <section>
        <div className="page-kicker">Team Travel Review</div>
        <h1 className="page-title">Business Trip Reviews</h1>
        <p className="page-subtitle">
          Review team business trips with destination, attachment, and date details.
        </p>
      </section>

      <Card
        className="page-panel table-card"
        title="Business Trip Reviews"
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchTrips}
            loading={loading}
          >
            Refresh
          </Button>
        }
      >
        <div className="responsive-desktop-table">
          <Table
            columns={columns}
            dataSource={data}
            rowKey="id"
            loading={loading}
            scroll={{ x: 700 }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: false,
              onChange: (page) => fetchTrips(page, pagination.pageSize),
            }}
            locale={{
              emptyText: !loading ? "No business trips found for your team." : "Loading..."
            }}
          />
        </div>
        <div className="responsive-mobile-list">
          <div className="responsive-record-list" aria-live="polite">
            {data.map((trip) => (
              <ResponsiveRecordCard
                key={trip.id}
                title={trip.user_name}
                badge={<Tag style={{ color: "var(--color-info)", background: "var(--color-info-soft)", border: "1px solid var(--color-info)" }}>{trip.city}</Tag>}
                onClick={() => setSelected(trip)}
                ariaLabel={`View ${trip.user_name}'s business trip`}
                footer={
                  <Button type="primary" ghost icon={<EyeOutlined />} onClick={() => setSelected(trip)}>
                    View Detail
                  </Button>
                }
              >
                <ResponsiveRecordRow label="Destination">
                  {trip.city}, {trip.country}
                </ResponsiveRecordRow>
                <ResponsiveRecordRow label="Start">
                  {dayjs(trip.start_date).format("DD/MM/YYYY")}
                </ResponsiveRecordRow>
                <ResponsiveRecordRow label="End">
                  {dayjs(trip.end_date).format("DD/MM/YYYY")}
                </ResponsiveRecordRow>
              </ResponsiveRecordCard>
            ))}
            {!loading && data.length === 0 && (
              <div className="responsive-empty-state">No business trips found for your team.</div>
            )}
          </div>
        </div>
      </Card>

      {/* DETAIL MODAL */}
      <Modal
        open={!!selected}
        onCancel={() => setSelected(null)}
        footer={null}
        width={600}
        title="Business Trip Detail"
      >
        {selected && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Employee">
              {selected.user_name}
            </Descriptions.Item>

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
                <Space>
                  <PaperClipOutlined />
                  <Text underline>
                    <a
                      href={getMediaUrl(selected.attachment_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View Attachment
                    </a>
                  </Text>
                </Space>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
