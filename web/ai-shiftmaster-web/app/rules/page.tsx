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
import { Department, ShiftRule } from '../types';
import { departmentService, shiftRuleService } from '../lib/services';
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

const ROLES = [
  'Any',
  'Software Engineer',
  'QA Engineer',
  'DevOps Engineer',
  'Developer',
  'Operations Specialist',
  'Logistics Coordinator',
  'Support Specialist',
  'Support Team Lead',
  'Support',
  'HR Specialist',
  'Recruiter',
  'Accountant',
  'Financial Analyst',
  'Manager',
];

const hhmm = (value: string) => value?.slice(0, 5);

export default function RulesPage() {
  const [rules, setRules] = useState<ShiftRule[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ShiftRule | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<number | undefined>(undefined);
  const [form] = Form.useForm();

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await shiftRuleService.getAll(
        selectedDepartment ? { department_id: selectedDepartment } : undefined
      );
      setRules(data.map((r) => ({ ...r, start_time: hhmm(r.start_time), end_time: hhmm(r.end_time) })));
    } catch {
      message.error('Failed to load shift rules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    departmentService.getAll().then(setDepartments).catch(() => message.error('Failed to load departments'));
  }, []);

  useEffect(() => {
    fetchRules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDepartment]);

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      role: 'Any',
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
      await shiftRuleService.delete(id);
      setRules((prev) => prev.filter((r) => r.id !== id));
      message.success('Shift rule deleted');
    } catch {
      message.error('Failed to delete shift rule');
    }
  };

  const handleToggleActive = async (id: number, is_active: boolean) => {
    try {
      await shiftRuleService.update(id, { is_active });
      setRules((prev) => prev.map((r) => (r.id === id ? { ...r, is_active } : r)));
      message.success(`Rule ${is_active ? 'activated' : 'deactivated'}`);
    } catch {
      message.error('Failed to update rule status');
    }
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    const ruleData: Partial<ShiftRule> = {
      name: values.name as string,
      department_id: values.department_id as number,
      role: values.role as string,
      start_time: (values.start_time as dayjs.Dayjs).format('HH:mm'),
      end_time: (values.end_time as dayjs.Dayjs).format('HH:mm'),
      min_employees: values.min_employees as number,
      max_employees: values.max_employees as number,
      days_of_week: values.days_of_week as number[],
      is_active: values.is_active as boolean,
    };
    if (ruleData.min_employees! > ruleData.max_employees!) {
      message.warning('Minimum employees cannot exceed maximum employees');
      return;
    }
    setSaving(true);
    try {
      if (editingRule) {
        await shiftRuleService.update(editingRule.id, ruleData);
        message.success('Shift rule updated');
      } else {
        await shiftRuleService.create(ruleData);
        message.success('Shift rule created');
      }
      setModalVisible(false);
      form.resetFields();
      fetchRules();
    } catch {
      message.error('Failed to save shift rule');
    } finally {
      setSaving(false);
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
                {departments.map((dept) => (
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
                    {departments.map((dept) => (
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
                <Button type="primary" htmlType="submit" loading={saving}>
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
