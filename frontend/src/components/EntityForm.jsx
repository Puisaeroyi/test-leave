import { Modal, Form, Input, Switch, Button, Row, Col, Divider } from 'antd';
import { useEffect, useState } from 'react';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';

const MAX_LOCATIONS = 5;
const MAX_DEPARTMENTS_PER_LOCATION = 5;
const MAX_ENTITY_DEPARTMENTS = 5;

const EntityForm = ({ visible, mode, entity, onCancel, onSuccess, submitting }) => {
  const [form] = Form.useForm();
  const [locationCount, setLocationCount] = useState(1);
  const [entityDeptCount, setEntityDeptCount] = useState(0);
  const [departmentsPerLocation, setDepartmentsPerLocation] = useState({});

  useEffect(() => {
    if (visible && mode === 'edit' && entity) {
      // Load entity's existing data
      const fetchData = async () => {
        try {
          const token = localStorage.getItem('access');
          const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

          const [locResponse, deptResponse] = await Promise.all([
            fetch(`${baseURL}/api/v1/organizations/locations/?entity_id=${entity.id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch(`${baseURL}/api/v1/organizations/departments/?entity_id=${entity.id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
          ]);

          const locationsData = await locResponse.json();
          const departmentsData = await deptResponse.json();

          const formValues = {
            entity_name: entity.entity_name,
            code: entity.code,
            is_active: entity.is_active,
          };

          // Group departments by location
          const locationDepts = {};
          const entityWideDepts = [];

          departmentsData.forEach(dept => {
            if (dept.location) {
              const locId = dept.location;
              if (!locationDepts[locId]) locationDepts[locId] = [];
              locationDepts[locId].push(dept);
            } else {
              entityWideDepts.push(dept);
            }
          });

          // Set locations and their departments
          locationsData.forEach((loc, index) => {
            const i = index + 1;
            formValues[`location_name_${i}`] = loc.location_name;
            formValues[`location_city_${i}`] = loc.city;
            formValues[`location_country_${i}`] = loc.country;
            formValues[`location_timezone_${i}`] = loc.timezone;

            const locDepts = locationDepts[loc.id] || [];
            setDepartmentsPerLocation(prev => ({ ...prev, [i]: locDepts.length }));

            locDepts.forEach((dept, deptIdx) => {
              const j = deptIdx + 1;
              formValues[`loc_${i}_dept_name_${j}`] = dept.department_name;
              formValues[`loc_${i}_dept_code_${j}`] = dept.code;
            });
          });

          setLocationCount(Math.max(locationsData.length, 1));
          setEntityDeptCount(entityWideDepts.length);

          // Set entity-wide departments
          entityWideDepts.forEach((dept, index) => {
            const i = index + 1;
            formValues[`entity_dept_name_${i}`] = dept.department_name;
            formValues[`entity_dept_code_${i}`] = dept.code;
          });

          form.setFieldsValue(formValues);
        } catch (error) {
          console.error('Failed to load entity data:', error);
        }
      };
      fetchData();
    } else if (visible && mode === 'create') {
      form.resetFields();
      form.setFieldsValue({ is_active: true });
      setLocationCount(1);
      setEntityDeptCount(0);
      setDepartmentsPerLocation({});
    }
  }, [visible, mode, entity, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      // Extract locations with their departments
      const locations = [];
      for (let i = 1; i <= locationCount; i++) {
        const locName = values[`location_name_${i}`];
        if (locName && locName.trim()) {
          const locDepts = [];
          const deptCount = departmentsPerLocation[i] || 0;

          for (let j = 1; j <= deptCount; j++) {
            const deptName = values[`loc_${i}_dept_name_${j}`];
            if (deptName && deptName.trim()) {
              locDepts.push({
                name: deptName.trim(),
                code: values[`loc_${i}_dept_code_${j}`]?.trim() || '',
              });
            }
          }

          locations.push({
            name: locName.trim(),
            city: values[`location_city_${i}`]?.trim() || 'HQ',
            country: values[`location_country_${i}`]?.trim() || 'USA',
            timezone: values[`location_timezone_${i}`]?.trim() || 'America/New_York',
            departments: locDepts,
          });
        }
      }

      // Extract entity-wide departments
      const entityWideDepts = [];
      for (let i = 1; i <= entityDeptCount; i++) {
        const deptName = values[`entity_dept_name_${i}`];
        if (deptName && deptName.trim()) {
          entityWideDepts.push({
            name: deptName.trim(),
            code: values[`entity_dept_code_${i}`]?.trim() || '',
          });
        }
      }

      // Prepare the payload
      const payload = {
        entity_name: values.entity_name,
        code: values.code,
        is_active: values.is_active,
        locations: locations,
        entity_wide_departments: entityWideDepts,
      };

      onSuccess(payload);
    } catch (error) {
      // Form validation errors are handled by Ant Design
    }
  };

  const addLocation = () => {
    if (locationCount < MAX_LOCATIONS) {
      setLocationCount(locationCount + 1);
    }
  };

  const removeLocation = () => {
    if (locationCount > 1) {
      setLocationCount(locationCount - 1);
    }
  };

  const addDepartmentToLocation = (locIndex) => {
    const currentCount = departmentsPerLocation[locIndex] || 0;
    if (currentCount < MAX_DEPARTMENTS_PER_LOCATION) {
      setDepartmentsPerLocation(prev => ({
        ...prev,
        [locIndex]: currentCount + 1
      }));
    }
  };

  const removeDepartmentFromLocation = (locIndex) => {
    const currentCount = departmentsPerLocation[locIndex] || 0;
    if (currentCount > 0) {
      setDepartmentsPerLocation(prev => ({
        ...prev,
        [locIndex]: currentCount - 1
      }));
    }
  };

  const addEntityDepartment = () => {
    if (entityDeptCount < MAX_ENTITY_DEPARTMENTS) {
      setEntityDeptCount(entityDeptCount + 1);
    }
  };

  const removeEntityDepartment = () => {
    if (entityDeptCount > 0) {
      setEntityDeptCount(entityDeptCount - 1);
    }
  };

  const renderLocationFields = () => {
    const locations = [];
    for (let i = 1; i <= locationCount; i++) {
      const deptCount = departmentsPerLocation[i] || 0;

      locations.push (
        <div key={`location-${i}`} style={{ marginBottom: 24, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>📍 Location {i} {i === 1 ? '(Required)' : '(Optional)'}</span>
            {i > 1 && (
              <Button size="small" danger onClick={() => removeLocation()}>
                Remove Location
              </Button>
            )}
          </div>

          {/* Location Details */}
          <Row gutter={8}>
            <Col span={12}>
              <Form.Item
                name={`location_name_${i}`}
                label="Location Name"
                rules={i === 1 ? [{ required: true, message: 'Required' }] : []}
                style={{ marginBottom: 8 }}
              >
                <Input placeholder="e.g., Headquarters" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={`location_city_${i}`}
                label="City"
                initialValue="HQ"
                style={{ marginBottom: 8 }}
              >
                <Input placeholder="City" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={8}>
            <Col span={12}>
              <Form.Item
                name={`location_country_${i}`}
                label="Country"
                initialValue="USA"
                style={{ marginBottom: 8 }}
              >
                <Input placeholder="Country" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={`location_timezone_${i}`}
                label="Timezone"
                initialValue="America/New_York"
                style={{ marginBottom: 8 }}
              >
                <Input placeholder="Timezone" />
              </Form.Item>
            </Col>
          </Row>

          {/* Departments for this Location */}
          <div style={{ marginTop: 16, padding: 12, backgroundColor: '#fff', borderRadius: 6 }}>
            <div style={{ fontWeight: 500, marginBottom: 8, fontSize: 13 }}>
              Departments for {form.getFieldValue(`location_name_${i}`) || `Location ${i}`}
            </div>

            {Array.from({ length: deptCount }, (_, j) => (
              <Row key={j} gutter={8} style={{ marginBottom: 8 }}>
                <Col span={12}>
                  <Form.Item
                    name={`loc_${i}_dept_name_${j + 1}`}
                    style={{ marginBottom: 0 }}
                  >
                    <Input placeholder={`Department ${j + 1} name`} />
                  </Form.Item>
                </Col>
                <Col span={10}>
                  <Form.Item
                    name={`loc_${i}_dept_code_${j + 1}`}
                    style={{ marginBottom: 0 }}
                  >
                    <Input
                      placeholder="Code"
                      style={{ textTransform: 'uppercase' }}
                      onChange={(e) => {
                        form.setFieldsValue({ [`loc_${i}_dept_code_${j + 1}`]: e.target.value.toUpperCase() });
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col span={2}>
                  <Button
                    size="small"
                    danger
                    icon={<MinusCircleOutlined />}
                    onClick={() => removeDepartmentFromLocation(i)}
                    style={{ width: '100%' }}
                  />
                </Col>
              </Row>
            ))}

            <Button
              type="dashed"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => addDepartmentToLocation(i)}
              disabled={deptCount >= MAX_DEPARTMENTS_PER_LOCATION}
              style={{ width: '100%' }}
            >
              Add Department ({deptCount}/{MAX_DEPARTMENTS_PER_LOCATION})
            </Button>
          </div>
        </div>
      );
    }
    return locations;
  };

  const renderEntityWideDepartments = () => {
    if (entityDeptCount === 0 && locationCount < MAX_LOCATIONS) return null;

    return (
      <div style={{ padding: 16, backgroundColor: '#e6f7ff', borderRadius: 8, border: '1px solid #91d5ff' }}>
        <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>🏢 Entity-Wide Departments</div>
        <div style={{ fontSize: 12, color: '#666', marginBottom: 12 }}>
          These departments are not tied to any specific location
        </div>

        {Array.from({ length: entityDeptCount }, (_, i) => (
          <Row key={i} gutter={8} style={{ marginBottom: 8 }}>
            <Col span={12}>
              <Form.Item
                name={`entity_dept_name_${i + 1}`}
                style={{ marginBottom: 0 }}
              >
                <Input placeholder={`Department ${i + 1} name`} />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item
                name={`entity_dept_code_${i + 1}`}
                style={{ marginBottom: 0 }}
              >
                <Input
                  placeholder="Code"
                  style={{ textTransform: 'uppercase' }}
                  onChange={(e) => {
                    form.setFieldsValue({ [`entity_dept_code_${i + 1}`]: e.target.value.toUpperCase() });
                  }}
                />
              </Form.Item>
            </Col>
            <Col span={2}>
              <Button
                size="small"
                danger
                icon={<MinusCircleOutlined />}
                onClick={removeEntityDepartment}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
        ))}

        <Button
          type="dashed"
          size="small"
          icon={<PlusOutlined />}
          onClick={addEntityDepartment}
          disabled={entityDeptCount >= MAX_ENTITY_DEPARTMENTS}
          style={{ width: '100%' }}
        >
          Add Entity-Wide Department ({entityDeptCount}/{MAX_ENTITY_DEPARTMENTS})
        </Button>
      </div>
    );
  };

  return (
    <Modal
      title={mode === 'create' ? 'Add New Entity' : 'Edit Entity'}
      open={visible}
      onOk={handleSubmit}
      onCancel={onCancel}
      okText={mode === 'create' ? 'Create' : 'Update'}
      confirmLoading={submitting}
      width={700}
      bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        {/* Entity Details */}
        <Divider orientation="left" style={{ fontSize: 14, margin: '8px 0 16px' }}>Entity Information</Divider>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="Entity Name"
              name="entity_name"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input placeholder="Acme Corporation" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="Entity Code"
              name="code"
              rules={[{ required: true, message: 'Required' }]}
            >
              <Input
                placeholder="ACME"
                style={{ textTransform: 'uppercase' }}
                onChange={(e) => {
                  form.setFieldsValue({ code: e.target.value.toUpperCase() });
                }}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* Locations with their Departments */}
        <Divider orientation="left" style={{ fontSize: 14, margin: '16px 0' }}>Locations & Departments</Divider>
        {renderLocationFields()}

        {locationCount < MAX_LOCATIONS && (
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={addLocation}
            style={{ width: '100%', marginBottom: 16 }}
          >
            Add Another Location ({locationCount}/{MAX_LOCATIONS})
          </Button>
        )}

        {/* Entity-Wide Departments */}
        {renderEntityWideDepartments()}

        <Form.Item
          label="Active"
          name="is_active"
          valuePropName="checked"
          style={{ marginTop: 16 }}
        >
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default EntityForm;
