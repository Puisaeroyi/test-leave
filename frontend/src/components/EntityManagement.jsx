import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, message, Typography
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { getEntities, createEntity, updateEntity, softDeleteEntity, getDeleteImpact } from '@api/entityApi';
import EntityForm from './EntityForm';

const { Text } = Typography;

const EntityManagement = () => {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);
  const [formMode, setFormMode] = useState('create');
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchEntities = async () => {
    setLoading(true);
    try {
      const data = await getEntities();
      setEntities(data.results || data);
    } catch (error) {
      message.error('Failed to load entities: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntities();
  }, []);

  const handleCreate = () => {
    setFormMode('create');
    setSelectedEntity(null);
    setFormVisible(true);
  };

  const handleEdit = (entity) => {
    setFormMode('edit');
    setSelectedEntity(entity);
    setFormVisible(true);
  };

  const handleFormSuccess = async (values) => {
    setSubmitting(true);
    try {
      if (formMode === 'create') {
        await createEntity(values);
        message.success('Entity created successfully');
      } else {
        await updateEntity(selectedEntity.id, values);
        message.success('Entity updated successfully');
      }
      setFormVisible(false);
      fetchEntities();
    } catch (error) {
      const errData = error.response?.data;
      const errMsg = errData?.error || errData?.entity_name?.[0] || errData?.code?.[0] || error.message;
      message.error('Failed to save entity: ' + errMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (entity) => {
    try {
      // Get impact first
      const impact = await getDeleteImpact(entity.id);

      // Show warning modal with cascade impact
      Modal.confirm({
        title: 'Deactivate Entity?',
        icon: <ExclamationCircleOutlined />,
        content: (
          <div>
            <p>This will deactivate <strong>{entity.entity_name}</strong> and cascade to:</p>
            <ul style={{ marginTop: 8, marginBottom: 8 }}>
              <li><strong>{impact.locations_count}</strong> Location{impact.locations_count !== 1 ? 's' : ''}</li>
              <li><strong>{impact.departments_count}</strong> Department{impact.departments_count !== 1 ? 's' : ''}</li>
            </ul>
            <p style={{ marginTop: 8 }}>
              Total impact: <strong>{impact.total_impact}</strong> record{impact.total_impact !== 1 ? 's' : ''}
            </p>
          </div>
        ),
        okText: 'Deactivate',
        okType: 'danger',
        cancelText: 'Cancel',
        onOk: async () => {
          try {
            const result = await softDeleteEntity(entity.id);
            message.success(
              `Deactivated ${result.entity_name} (${result.locations_deactivated} locations, ${result.departments_deactivated} departments)`
            );
            fetchEntities();
          } catch (error) {
            message.error('Failed to deactivate: ' + (error.response?.data?.error || error.message));
          }
        }
      });
    } catch (error) {
      message.error('Failed to check impact: ' + (error.response?.data?.error || error.message));
    }
  };

  const columns = [
    {
      title: 'Entity Name',
      dataIndex: 'entity_name',
      key: 'entity_name',
      sorter: (a, b) => a.entity_name.localeCompare(b.entity_name),
    },
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: 'Locations',
      dataIndex: 'locations_count',
      key: 'locations_count',
      width: 100,
      align: 'center',
      render: (count) => count || 0,
    },
    {
      title: 'Departments',
      dataIndex: 'departments_count',
      key: 'departments_count',
      width: 120,
      align: 'center',
      render: (count) => count || 0,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Active' : 'Inactive'}
        </Tag>
      ),
      filters: [
        { text: 'Active', value: true },
        { text: 'Inactive', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Edit
          </Button>
          {record.is_active && (
            <Button
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
              danger
              size="small"
            >
              Delete
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="Entity Management"
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          Add Entity
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={entities}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />

      <EntityForm
        visible={formVisible}
        mode={formMode}
        entity={selectedEntity}
        onCancel={() => setFormVisible(false)}
        onSuccess={handleFormSuccess}
        submitting={submitting}
      />
    </Card>
  );
};

export default EntityManagement;
