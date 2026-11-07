'use client';

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Select,
  Tag,
  Typography,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  DatePicker,
  TimePicker,
  Tabs,
  Badge,
  Alert,
  Calendar,
  Tooltip,
  Spin,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined,
  CalendarOutlined,
  UnorderedListOutlined,
  ReloadOutlined,
  TeamOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Dayjs } from 'dayjs';
import DashboardLayout from '../components/DashboardLayout';
import { Shift, ShiftConflict, Employee, Department } from '../types';
import { shiftService, employeeService, departmentService } from '../lib/services';
import { apiErrorMessage } from '../lib/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface ShiftFormValues {
  employee_id: number;
  department_id: number;
  date: Dayjs;
  time_range: [Dayjs, Dayjs];
  status?: Shift['status'];
}

export default function ShiftsPage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [conflicts, setConflicts] = useState<ShiftConflict[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingShift, setEditingShift] = useState<Shift | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<number | undefined>();
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({ page: 1, pageSize: 50, total: 0 });

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: { page: number; page_size: number; department_id?: number; start_date?: string; end_date?: string } = {
        page: pagination.page,
        page_size: pagination.pageSize,
      };
      if (selectedDepartment) params.department_id = selectedDepartment;
      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD');
        params.end_date = dateRange[1].format('YYYY-MM-DD');
      }

      const shiftResponse = await shiftService.getAll(params);
      setShifts(shiftResponse.items);
      setPagination(prev => ({ ...prev, total: shiftResponse.total }));

      const empResponse = await employeeService.getAll({ page: 1, page_size: 500 });
      setEmployees(empResponse.items);

      const deptResponse = await departmentService.getAll();
      setDepartments(deptResponse);

      if (dateRange) {
        try {
          const conflictsData = await shiftService.getConflicts({
            start_date: dateRange[0].format('YYYY-MM-DD'),
            end_date: dateRange[1].format('YYYY-MM-DD'),
          });
          setConflicts(conflictsData || []);
        } catch { setConflicts([]); }
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      message.error('Failed to load shifts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [pagination.page, pagination.pageSize, selectedDepartment, dateRange]);

  const handleCreate = () => { setEditingShift(null); form.resetFields(); setIsModalOpen(true); };

  const handleEdit = (shift: Shift) => {
    setEditingShift(shift);
    form.setFieldsValue({
      employee_id: shift.employee_id,
      department_id: shift.department_id,
      date: dayjs(shift.start_time),
      time_range: [dayjs(shift.start_time), dayjs(shift.end_time)],
      status: shift.status,
    });
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try { await shiftService.delete(id); message.success('Shift deleted'); fetchData(); }
    catch { message.error('Failed to delete shift'); }
  };

  const handleSubmit = async (values: ShiftFormValues) => {
    try {
      const shiftData = {
        employee_id: values.employee_id,
        department_id: values.department_id,
        start_time: values.date.hour(values.time_range[0].hour()).minute(values.time_range[0].minute()).toISOString(),
        end_time: values.date.hour(values.time_range[1].hour()).minute(values.time_range[1].minute()).toISOString(),
        status: values.status || 'scheduled',
      };
      if (editingShift) { await shiftService.update(editingShift.id, shiftData); message.success('Shift updated'); }
      else { await shiftService.create(shiftData); message.success('Shift created'); }
      setIsModalOpen(false); form.resetFields(); fetchData();
    } catch (error) { message.error(apiErrorMessage(error, 'Operation failed')); }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'cancelled': return 'red';
      case 'in_progress': return 'blue';
      default: return 'orange';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'cancelled': return 'Cancelled';
      case 'in_progress': return 'In progress';
      case 'scheduled': return 'Scheduled';
      default: return status;
    }
  };

  const columns: ColumnsType<Shift> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Employee', dataIndex: 'employee_name', key: 'employee_name', render: (name: string) => <Text strong>{name}</Text> },
    { title: 'Department', dataIndex: 'department_name', key: 'department_name', render: (name: string) => <Tag color="blue">{name}</Tag> },
    { title: 'Date', dataIndex: 'start_time', key: 'date', render: (start_time: string) => dayjs(start_time).format('YYYY-MM-DD (ddd)'), sorter: (a, b) => dayjs(a.start_time).unix() - dayjs(b.start_time).unix() },
    { title: 'Time', key: 'time', render: (_, record) => <Text>{dayjs(record.start_time).format('HH:mm')} - {dayjs(record.end_time).format('HH:mm')}</Text> },
    { title: 'Duration', key: 'duration', render: (_, record) => { const hours = dayjs(record.end_time).diff(dayjs(record.start_time), 'hour', true); return <Tag>{hours.toFixed(1)} h</Tag>; } },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (status: string) => <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>, filters: [{ text: 'Scheduled', value: 'scheduled' }, { text: 'In progress', value: 'in_progress' }, { text: 'Completed', value: 'completed' }, { text: 'Cancelled', value: 'cancelled' }], onFilter: (value, record) => record.status === value },
    { title: 'Actions', key: 'actions', width: 120, render: (_, record) => (
      <Space>
        <Tooltip title="Edit"><Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)} /></Tooltip>
        <Popconfirm title="Delete this shift?" onConfirm={() => handleDelete(record.id)} okText="Delete" cancelText="Cancel">
          <Tooltip title="Delete"><Button type="text" danger icon={<DeleteOutlined />} /></Tooltip>
        </Popconfirm>
      </Space>
    ) },
  ];

  const dateCellRender = (value: Dayjs) => {
    const dayShifts = shifts.filter((shift) => dayjs(shift.start_time).format('YYYY-MM-DD') === value.format('YYYY-MM-DD'));
    if (dayShifts.length === 0) return null;
    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {dayShifts.slice(0, 3).map((shift) => (
          <li key={shift.id} style={{ marginBottom: 2 }}>
            <Tooltip title={`${shift.employee_name}: ${dayjs(shift.start_time).format('HH:mm')} - ${dayjs(shift.end_time).format('HH:mm')}`}>
              <Tag color={getStatusColor(shift.status)} style={{ fontSize: 10, padding: '0 4px', marginRight: 0 }}>{shift.employee_name?.split(' ')[0]}</Tag>
            </Tooltip>
          </li>
        ))}
        {dayShifts.length > 3 && <li><Text type="secondary" style={{ fontSize: 10 }}>+{dayShifts.length - 3} more</Text></li>}
      </ul>
    );
  };

  const todayShifts = shifts.filter((s) => dayjs(s.start_time).format('YYYY-MM-DD') === dayjs().format('YYYY-MM-DD'));
  const scheduledShifts = shifts.filter((s) => s.status === 'scheduled');
  const totalHours = shifts.reduce((sum, s) => sum + dayjs(s.end_time).diff(dayjs(s.start_time), 'hour', true), 0);

  return (
    <DashboardLayout>
      <Spin spinning={loading}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <Title level={4} style={{ margin: 0 }}>Shift Management</Title>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>New shift</Button>
            </Space>
          </div>

          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Total shifts" value={pagination.total} prefix={<CalendarOutlined />} /></Card></Col>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Today's shifts" value={todayShifts.length} prefix={<TeamOutlined />} valueStyle={{ color: '#1890ff' }} /></Card></Col>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Scheduled" value={scheduledShifts.length} prefix={<ClockCircleOutlined />} valueStyle={{ color: '#faad14' }} /></Card></Col>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Total hours" value={totalHours.toFixed(1)} suffix="h" valueStyle={{ color: '#52c41a' }} /></Card></Col>
          </Row>

          {conflicts.length > 0 && (
            <Alert message={`${conflicts.length} shift conflict(s) detected`} description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {conflicts.slice(0, 3).map((conflict, index) => (<li key={index}><Tag color={conflict.type === 'overtime' ? 'orange' : 'red'}>{conflict.type.toUpperCase()}</Tag>{conflict.message}</li>))}
                {conflicts.length > 3 && <li>…and {conflicts.length - 3} more</li>}
              </ul>
            } type="warning" showIcon icon={<WarningOutlined />} style={{ marginBottom: 24 }} />
          )}

          <Card bordered={false} style={{ marginBottom: 24 }}>
            <Row gutter={16} align="middle">
              <Col xs={24} sm={8}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Date range</Text>
                <RangePicker value={dateRange} onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])} style={{ width: '100%' }} />
              </Col>
              <Col xs={24} sm={8}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Department</Text>
                <Select placeholder="All departments" style={{ width: '100%' }} value={selectedDepartment} onChange={setSelectedDepartment} allowClear>
                  {departments.map((dept) => (<Option key={dept.id} value={dept.id}>{dept.name}</Option>))}
                </Select>
              </Col>
              <Col xs={24} sm={8}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>View</Text>
                <Tabs activeKey={viewMode} onChange={(key) => setViewMode(key as 'list' | 'calendar')} items={[
                  { key: 'list', label: <><UnorderedListOutlined /> List</> },
                  { key: 'calendar', label: <><CalendarOutlined /> Calendar</> },
                ]} />
              </Col>
            </Row>
          </Card>

          <Card bordered={false}>
            {viewMode === 'list' ? (
              <Table columns={columns} dataSource={shifts} rowKey="id" pagination={{
                current: pagination.page, pageSize: pagination.pageSize, total: pagination.total,
                showSizeChanger: true, showTotal: (total) => `${total} shifts`,
                onChange: (page, pageSize) => setPagination({ ...pagination, page, pageSize }),
              }} />
            ) : (
              <Calendar dateCellRender={dateCellRender} />
            )}
          </Card>

          <Modal title={editingShift ? 'Edit shift' : 'New shift'} open={isModalOpen} onCancel={() => { setIsModalOpen(false); form.resetFields(); }} footer={null} width={600}>
            <Form form={form} layout="vertical" onFinish={handleSubmit}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="employee_id" label="Employee" rules={[{ required: true, message: 'Select an employee' }]}>
                    <Select placeholder="Select an employee" showSearch optionFilterProp="children">
                      {employees.map((emp) => (<Option key={emp.id} value={emp.id}>{emp.name} - {emp.department_name}</Option>))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="department_id" label="Department" rules={[{ required: true, message: 'Select a department' }]}>
                    <Select placeholder="Select a department">{departments.map((dept) => (<Option key={dept.id} value={dept.id}>{dept.name}</Option>))}</Select>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="date" label="Date" rules={[{ required: true, message: 'Select a date' }]}>
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="time_range" label="Time range" rules={[{ required: true, message: 'Select a time range' }]}>
                    <TimePicker.RangePicker format="HH:mm" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              {editingShift && (
                <Form.Item name="status" label="Status">
                  <Select>
                    <Option value="scheduled">Scheduled</Option>
                    <Option value="in_progress">In progress</Option>
                    <Option value="completed">Completed</Option>
                    <Option value="cancelled">Cancelled</Option>
                  </Select>
                </Form.Item>
              )}
              <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                <Space>
                  <Button onClick={() => setIsModalOpen(false)}>Cancel</Button>
                  <Button type="primary" htmlType="submit">{editingShift ? 'Update' : 'Create'}</Button>
                </Space>
              </Form.Item>
            </Form>
          </Modal>
        </div>
      </Spin>
    </DashboardLayout>
  );
}
