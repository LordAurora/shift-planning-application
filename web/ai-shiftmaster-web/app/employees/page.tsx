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
  Tooltip,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  KeyOutlined,
  CopyOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import DashboardLayout from '../components/DashboardLayout';
import { Employee, Department, AvailabilitySlot } from '../types';
import { employeeService, departmentService } from '../lib/services';
import { apiErrorMessage } from '../lib/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

const ROLES = [
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

const SHIFT_LABELS: Record<string, { label: string; color: string }> = {
  morning: { label: 'Morning', color: 'gold' },
  day: { label: 'Day', color: 'green' },
  afternoon: { label: 'Evening', color: 'blue' },
  night: { label: 'Night', color: 'purple' },
};

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [searchText, setSearchText] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState<number | undefined>(undefined);
  const [showPassword, setShowPassword] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [form] = Form.useForm();

  // Password generator function
  const generatePassword = () => {
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    const special = '!@#$%&*';
    const allChars = lowercase + uppercase + numbers + special;
    
    let password = '';
    // Ensure at least one of each type
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += special[Math.floor(Math.random() * special.length)];
    
    // Fill rest with random characters
    for (let i = 0; i < 8; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)];
    }
    
    // Shuffle the password
    password = password.split('').sort(() => Math.random() - 0.5).join('');
    
    setGeneratedPassword(password);
    form.setFieldValue('password', password);
    message.success('Random password generated');
  };

  const copyPassword = () => {
    const password = form.getFieldValue('password');
    if (password) {
      navigator.clipboard.writeText(password);
      message.success('Password copied to clipboard');
    }
  };

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await employeeService.getAll({
        page: pagination.current,
        page_size: pagination.pageSize,
        department_id: selectedDepartment,
        search: searchText || undefined,
      });
      setEmployees(response.items);
      setPagination(prev => ({ ...prev, total: response.total }));
    } catch (error) {
      message.error('Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getAll();
      setDepartments(response);
    } catch (error) {
      message.error('Failed to load departments');
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [selectedDepartment, searchText, pagination.current, pagination.pageSize]);

  const handleCreate = () => {
    setEditingEmployee(null);
    setGeneratedPassword('');
    form.resetFields();
    form.setFieldsValue({
      weekly_working_limit: 40,
      overtime_limit: 10,
      availability_days: [1, 2, 3, 4, 5],
      availability_start: dayjs('09:00', 'HH:mm'),
      availability_end: dayjs('17:00', 'HH:mm'),
    });
    setModalVisible(true);
  };

  const handleEdit = (record: Employee) => {
    setEditingEmployee(record);
    setGeneratedPassword('');
    const availableDays = record.availability?.map(a => a.day) || [];
    const firstSlot = record.availability?.[0];
    form.setFieldsValue({
      ...record,
      password: '', // Clear password field on edit
      availability_days: availableDays,
      availability_start: firstSlot ? dayjs(firstSlot.start_time, 'HH:mm') : dayjs('09:00', 'HH:mm'),
      availability_end: firstSlot ? dayjs(firstSlot.end_time, 'HH:mm') : dayjs('17:00', 'HH:mm'),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await employeeService.delete(id);
      message.success('Employee deleted');
      fetchEmployees();
    } catch (error) {
      message.error('Failed to delete employee');
    }
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    try {
      const availability: AvailabilitySlot[] = ((values.availability_days as number[] | undefined) ?? []).map(day => ({
        day,
        start_time: (values.availability_start as dayjs.Dayjs).format('HH:mm'),
        end_time: (values.availability_end as dayjs.Dayjs).format('HH:mm'),
      }));

      const employeeData: Partial<Employee> & { password?: string } = {
        name: values.name as string,
        email: values.email as string,
        role: values.role as string,
        department_id: values.department_id as number,
        weekly_working_limit: values.weekly_working_limit as number,
        overtime_limit: values.overtime_limit as number,
        availability,
      };

      if (editingEmployee) {
        // Only include password if it was changed
        if (values.password) {
          employeeData.password = values.password as string;
        }
        await employeeService.update(editingEmployee.id, employeeData);
        message.success('Employee updated');
      } else {
        // Password is required for new employees
        employeeData.password = values.password as string;
        await employeeService.create(employeeData);
        message.success('Employee created');
      }
      setModalVisible(false);
      form.resetFields();
      fetchEmployees();
    } catch (error) {
      message.error(apiErrorMessage(error, 'Failed to save employee'));
    }
  };

  const columns: ColumnsType<Employee> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => <Tag color="blue">{role}</Tag>,
    },
    {
      title: 'Department',
      dataIndex: 'department_name',
      key: 'department_name',
    },
    {
      title: 'Weekly limit',
      dataIndex: 'weekly_working_limit',
      key: 'weekly_working_limit',
      render: (hours: number) => `${hours} h`,
    },
    {
      title: 'Overtime limit',
      dataIndex: 'overtime_limit',
      key: 'overtime_limit',
      render: (hours: number) => `${hours} h`,
    },
    {
      title: 'Preferences',
      key: 'preferences',
      render: (_: unknown, record: Employee) => {
        const pref = record.preferences;
        const shift = pref?.preferred_shift ? SHIFT_LABELS[pref.preferred_shift] : null;
        const off = pref?.weekly_off_day != null ? DAYS_OF_WEEK.find((d) => d.value === pref.weekly_off_day)?.label : null;
        if (!shift && !off) {
          const days = record.availability?.map((a) => DAYS_OF_WEEK.find((d) => d.value === a.day)?.label.slice(0, 3)).join(', ');
          return <Text type="secondary">{days || 'Any day'}</Text>;
        }
        return (
          <Space size={4} wrap>
            {shift && <Tag color={shift.color}>{shift.label}</Tag>}
            {off && <Tag>Off: {off.slice(0, 3)}</Tag>}
          </Space>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete employee"
            description="Delete this employee? Their user account will be removed too."
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            cancelText="Cancel"
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
            Employees
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Add employee
          </Button>
        </div>

        <Card bordered={false} style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="Search by name or email..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
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
            <Col xs={24} sm={12} md={8}>
              <Button icon={<ReloadOutlined />} onClick={fetchEmployees}>
                Refresh
              </Button>
            </Col>
          </Row>
        </Card>

        <Card bordered={false}>
          <Spin spinning={loading}>
            <Table
              columns={columns}
              dataSource={employees}
              rowKey="id"
              pagination={{
                current: pagination.current,
                pageSize: pagination.pageSize,
                total: pagination.total,
                showSizeChanger: true,
                showTotal: (total) => `${total} employees`,
                onChange: (page, pageSize) => setPagination(prev => ({ ...prev, current: page, pageSize })),
              }}
            />
          </Spin>
        </Card>

        <Modal
          title={editingEmployee ? 'Edit employee' : 'Add employee'}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
          }}
          footer={null}
          width={700}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            style={{ marginTop: 24 }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="name"
                  label="Full name"
                  rules={[{ required: true, message: 'Please enter a name' }]}
                >
                  <Input placeholder="Ornek: Ahmet Yilmaz" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="email"
                  label="Email (used to sign in)"
                  rules={[
                    { required: true, message: 'Please enter an email' },
                    { type: 'email', message: 'Enter a valid email address' },
                  ]}
                >
                  <Input placeholder="ornek@sirket.com" />
                </Form.Item>
              </Col>
            </Row>

            {/* Password Field with Generator */}
            <Form.Item
              name="password"
              label={
                <Space>
                  <span>{editingEmployee ? 'New password (leave empty to keep)' : 'Password (for the mobile app)'}</span>
                  <Tooltip title="The employee uses this password to sign in to the mobile app">
                    <KeyOutlined style={{ color: '#1e3a5f' }} />
                  </Tooltip>
                </Space>
              }
              rules={editingEmployee ? [] : [
                { required: true, message: 'Please enter a password' },
                { min: 6, message: 'Password must be at least 6 characters' },
              ]}
            >
              <Input.Group compact style={{ display: 'flex' }}>
                <Input
                  style={{ flex: 1 }}
                  type={showPassword ? 'text' : 'password'}
                  placeholder={editingEmployee ? 'New password (optional)' : 'Enter or generate a password'}
                  value={form.getFieldValue('password')}
                  onChange={(e) => form.setFieldValue('password', e.target.value)}
                  suffix={
                    <Space>
                      <Tooltip title={showPassword ? 'Hide password' : 'Show password'}>
                        <Button
                          type="text"
                          size="small"
                          icon={showPassword ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                          onClick={() => setShowPassword(!showPassword)}
                        />
                      </Tooltip>
                      <Tooltip title="Copy password">
                        <Button
                          type="text"
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={copyPassword}
                        />
                      </Tooltip>
                    </Space>
                  }
                />
                <Tooltip title="Generate a strong random password">
                  <Button
                    type="primary"
                    icon={<KeyOutlined />}
                    onClick={generatePassword}
                    style={{ backgroundColor: '#22c55e', borderColor: '#22c55e' }}
                  >
                    Generate
                  </Button>
                </Tooltip>
              </Input.Group>
            </Form.Item>
            {generatedPassword && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f0fdf4', borderRadius: 8, border: '1px solid #22c55e' }}>
                <Text type="secondary">Generated password: </Text>
                <Text strong copyable style={{ color: '#22c55e' }}>{generatedPassword}</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>Share this password with the employee for mobile sign-in.</Text>
              </div>
            )}

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="role"
                  label="Role"
                  rules={[{ required: true, message: 'Please select a role' }]}
                >
                  <Select placeholder="Select a role">
                    {ROLES.map((role) => (
                      <Option key={role} value={role}>
                        {role}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="department_id"
                  label="Department"
                  rules={[{ required: true, message: 'Please select a department' }]}
                >
                  <Select placeholder="Select a department">
                    {departments.map((dept) => (
                      <Option key={dept.id} value={dept.id}>
                        {dept.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="weekly_working_limit"
                  label="Weekly working limit (hours)"
                  rules={[{ required: true, message: 'Please enter a weekly limit' }]}
                >
                  <InputNumber min={0} max={168} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="overtime_limit"
                  label="Overtime limit (hours)"
                  rules={[{ required: true, message: 'Please enter an overtime limit' }]}
                >
                  <InputNumber min={0} max={40} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="availability_days"
              label="Available days"
              tooltip="Leave empty if the employee can work any day"
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

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="availability_start"
                  label="Available from"
                  rules={[{ required: true, message: 'Please select a start time' }]}
                >
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="availability_end"
                  label="Available until"
                  rules={[{ required: true, message: 'Please select an end time' }]}
                >
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
              <Space style={{ float: 'right' }}>
                <Button onClick={() => setModalVisible(false)}>Cancel</Button>
                <Button type="primary" htmlType="submit">
                  {editingEmployee ? 'Update' : 'Create'}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
