'use client';

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Tag,
  Typography,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  TimePicker,
  Checkbox,
  Switch,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import DashboardLayout from '../components/DashboardLayout';
import { ShiftRule } from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday', short: 'Sun' },
  { value: 1, label: 'Monday', short: 'Mon' },
  { value: 2, label: 'Tuesday', short: 'Tue' },
  { value: 3, label: 'Wednesday', short: 'Wed' },
  { value: 4, label: 'Thursday', short: 'Thu' },
  { value: 5, label: 'Friday', short: 'Fri' },
  { value: 6, label: 'Saturday', short: 'Sat' },
];

const ROLES = ['Developer', 'Manager', 'Analyst', 'Designer', 'Support', 'Administrator', 'Any'];

const mockDepartments = [
  { id: 1, name: 'Engineering' },
  { id: 2, name: 'Operations' },
  { id: 3, name: 'Customer Service' },
  { id: 4, name: 'HR' },
];

const mockRules: ShiftRule[] = [
  {
    id: 1,
    name: 'Morning Shift - Engineering',
    department_id: 1,
    department_name: 'Engineering',
    role: 'Developer',
    start_time: '09:00',
    end_time: '17:00',
    min_employees: 2,
    max_employees: 5,
    days_of_week: [1, 2, 3, 4, 5],
    is_active: true,
    created_at: '2025-01-01',
  },
  {
    id: 2,
    name: 'Support Shift',
    department_id: 3,
    department_name: 'Customer Service',
    role: 'Support',
    start_time: '08:00',
    end_time: '20:00',
    min_employees: 3,
    max_employees: 8,
    days_of_week: [0, 1, 2, 3, 4, 5, 6],
    is_active: true,
    created_at: '2025-01-01',
  },
  {
    id: 3,
    name: 'Operations Day Shift',
    department_id: 2,
    department_name: 'Operations',
    role: 'Any',
    start_time: '06:00',
    end_time: '14:00',
    min_employees: 4,
    max_employees: 10,
    days_of_week: [1, 2, 3, 4, 5],
    is_active: true,
    created_at: '2025-01-02',
  },
  {
    id: 4,
    name: 'Weekend Coverage',
    department_id: 2,
    department_name: 'Operations',
    role: 'Any',
    start_time: '10:00',
    end_time: '18:00',
    min_employees: 2,
    max_employees: 4,
    days_of_week: [0, 6],
    is_active: false,
    created_at: '2025-01-03',
  },
];

export default function RulesPage() {
  const [rules, setRules] = useState<ShiftRule[]>(mockRules);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ShiftRule | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<number | undefined>(undefined);
  const [form] = Form.useForm();

  const fetchRules = async () => {
    setLoading(true);
    try {
      let filtered = mockRules;
      if (selectedDepartment) {
        filtered = filtered.filter((r) => r.department_id === selectedDepartment);
      }
      setRules(filtered);
    } catch (error) {
      message.error('Failed to fetch shift rules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [selectedDepartment]);

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      min_employees: 1,
      max_employees: 5,
      days_of_week: [1, 2, 3, 4, 5],
      start_time: dayjs('09:00', 'HH:mm'),
      end_time: dayjs('17:00', 'HH:mm'),
      is_active: true,
    });
    setModalVisible(true);
  };

  const handleEdit = (record: ShiftRule) => {
    setEditingRule(record);
    form.setFieldsValue({
      ...record,
      start_time: dayjs(record.start_time, 'HH:mm'),
      end_time: dayjs(record.end_time, 'HH:mm'),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      setRules(rules.filter((r) => r.id !== id));
      message.success('Shift rule deleted successfully');
    } catch (error) {
      message.error('Failed to delete shift rule');
    }
  };

  const handleToggleActive = async (id: number, is_active: boolean) => {
    try {
      setRules(
        rules.map((r) => (r.id === id ? { ...r, is_active } : r))
      );
      message.success(`Rule ${is_active ? 'activated' : 'deactivated'} successfully`);
    } catch (error) {
      message.error('Failed to update rule status');
    }
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    try {
      const department = mockDepartments.find((d) => d.id === values.department_id);

      const ruleData: Partial<ShiftRule> = {
        name: values.name as string,
        department_id: values.department_id as number,
        department_name: department?.name,
        role: values.role as string,
        start_time: (values.start_time as dayjs.Dayjs).format('HH:mm'),
        end_time: (values.end_time as dayjs.Dayjs).format('HH:mm'),
        min_employees: values.min_employees as number,
        max_employees: values.max_employees as number,
        days_of_week: values.days_of_week as number[],
        is_active: values.is_active as boolean,
      };

      if (editingRule) {
        const updated = rules.map((r) =>
          r.id === editingRule.id ? { ...r, ...ruleData } : r
        );
        setRules(updated);
        message.success('Shift rule updated successfully');
      } else {
        const newRule: ShiftRule = {
          ...ruleData,
          id: Math.max(...rules.map((r) => r.id)) + 1,
          created_at: new Date().toISOString(),
        } as ShiftRule;
        setRules([...rules, newRule]);
        message.success('Shift rule created successfully');
      }
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('Failed to save shift rule');
    }
  };

  const columns: ColumnsType<ShiftRule> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Department',
      dataIndex: 'department_name',
      key: 'department_name',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => <Tag color="blue">{role}</Tag>,
    },
    {
      title: 'Time Range',
      key: 'time_range',
      render: (_, record) => `${record.start_time} - ${record.end_time}`,
    },
    {
      title: 'Employees',
      key: 'employees',
      render: (_, record) => `${record.min_employees} - ${record.max_employees}`,
    },
    {
      title: 'Days',
      dataIndex: 'days_of_week',
      key: 'days_of_week',
      render: (days: number[]) => (
        <span>
          {days.map((d) => DAYS_OF_WEEK.find((day) => day.value === d)?.short).join(', ')}
        </span>
      ),
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active: boolean, record) => (
        <Switch
          checked={is_active}
          onChange={(checked) => handleToggleActive(record.id, checked)}
          size="small"
        />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="Delete Rule"
            description="Are you sure you want to delete this rule?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0 }}>
            Shift Rules
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Add Rule
          </Button>
        </div>

        <Card bordered={false} style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Select
                placeholder="Filter by department"
                style={{ width: '100%' }}
                value={selectedDepartment}
                onChange={setSelectedDepartment}
                allowClear
              >
                {mockDepartments.map((dept) => (
                  <Option key={dept.id} value={dept.id}>
                    {dept.name}
                  </Option>
                ))}
              </Select>
            </Col>
          </Row>
        </Card>

        <Card bordered={false}>
          <Table
            columns={columns}
            dataSource={rules}
            loading={loading}
            rowKey="id"
            pagination={{
              defaultPageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} rules`,
            }}
          />
        </Card>

        <Modal
          title={editingRule ? 'Edit Shift Rule' : 'Add Shift Rule'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
          }}
          footer={null}
          width={600}
        >
          <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ marginTop: 24 }}>
            <Form.Item
              name="name"
              label="Rule Name"
              rules={[{ required: true, message: 'Please enter rule name' }]}
            >
              <Input placeholder="e.g., Morning Shift - Engineering" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="department_id"
                  label="Department"
                  rules={[{ required: true, message: 'Please select department' }]}
                >
                  <Select placeholder="Select department">
                    {mockDepartments.map((dept) => (
                      <Option key={dept.id} value={dept.id}>
                        {dept.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="role"
                  label="Role"
                  rules={[{ required: true, message: 'Please select role' }]}
                >
                  <Select placeholder="Select role">
                    {ROLES.map((role) => (
                      <Option key={role} value={role}>
                        {role}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="start_time"
                  label="Start Time"
                  rules={[{ required: true, message: 'Please select start time' }]}
                >
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="end_time"
                  label="End Time"
                  rules={[{ required: true, message: 'Please select end time' }]}
                >
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="min_employees"
                  label="Minimum Employees"
                  rules={[{ required: true, message: 'Please enter minimum employees' }]}
                >
                  <InputNumber min={1} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="max_employees"
                  label="Maximum Employees"
                  rules={[{ required: true, message: 'Please enter maximum employees' }]}
                >
                  <InputNumber min={1} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="days_of_week"
              label="Active Days"
              rules={[{ required: true, message: 'Please select at least one day' }]}
            >
              <Checkbox.Group>
                <Row>
                  {DAYS_OF_WEEK.map((day) => (
                    <Col span={8} key={day.value}>
                      <Checkbox value={day.value}>{day.label}</Checkbox>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Form.Item>

            <Form.Item name="is_active" label="Active" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
              <Space style={{ float: 'right' }}>
                <Button onClick={() => setModalVisible(false)}>Cancel</Button>
                <Button type="primary" htmlType="submit">
                  {editingRule ? 'Update' : 'Create'}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
