import { useState, useEffect } from "react";
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

const { Text } = Typography;

export default function BusinessTripTickets() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // Fetch team business trips on mount
  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async (page = 1, pageSize = 10) => {
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
  };

  const columns = [
    {
      title: "Employee Name",
      dataIndex: "user_name",
      align: "center",
      render: (v) => <Text strong>{v}</Text>,
    },
    {
      title: "Destination",
      render: (_, r) => <Tag color="geekblue">{r.city}, {r.country}</Tag>,
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
    <>
      <Card
        title="Business Trip Tickets"
        style={{ borderRadius: 16 }}
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
    </>
  );
}
