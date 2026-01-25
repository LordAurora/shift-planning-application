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
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

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
      const params: any = { page: pagination.page, page_size: pagination.pageSize };
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
      console.error('Veri yuklenirken hata:', error);
      message.error('Veriler yuklenirken hata olustu');
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
    try { await shiftService.delete(id); message.success('Vardiya silindi'); fetchData(); }
    catch { message.error('Vardiya silinemedi'); }
  };

  const handleSubmit = async (values: any) => {
    try {
      const shiftData = {
        employee_id: values.employee_id,
        department_id: values.department_id,
        start_time: values.date.hour(values.time_range[0].hour()).minute(values.time_range[0].minute()).toISOString(),
        end_time: values.date.hour(values.time_range[1].hour()).minute(values.time_range[1].minute()).toISOString(),
        status: values.status || 'scheduled',
      };
      if (editingShift) { await shiftService.update(editingShift.id, shiftData); message.success('Vardiya guncellendi'); }
      else { await shiftService.create(shiftData); message.success('Vardiya olusturuldu'); }
      setIsModalOpen(false); form.resetFields(); fetchData();
    } catch (error: any) { message.error(error?.response?.data?.detail || 'Islem basarisiz'); }
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
      case 'completed': return 'Tamamlandi';
      case 'cancelled': return 'Iptal Edildi';
      case 'in_progress': return 'Devam Ediyor';
      case 'scheduled': return 'Planli';
      default: return status;
    }
  };

  const columns: ColumnsType<Shift> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Calisan', dataIndex: 'employee_name', key: 'employee_name', render: (name: string) => <Text strong>{name}</Text> },
    { title: 'Departman', dataIndex: 'department_name', key: 'department_name', render: (name: string) => <Tag color="blue">{name}</Tag> },
    { title: 'Tarih', dataIndex: 'start_time', key: 'date', render: (start_time: string) => dayjs(start_time).format('YYYY-MM-DD (ddd)'), sorter: (a, b) => dayjs(a.start_time).unix() - dayjs(b.start_time).unix() },
    { title: 'Saat', key: 'time', render: (_, record) => <Text>{dayjs(record.start_time).format('HH:mm')} - {dayjs(record.end_time).format('HH:mm')}</Text> },
    { title: 'Sure', key: 'duration', render: (_, record) => { const hours = dayjs(record.end_time).diff(dayjs(record.start_time), 'hour', true); return <Tag>{hours.toFixed(1)} saat</Tag>; } },
    { title: 'Durum', dataIndex: 'status', key: 'status', render: (status: string) => <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>, filters: [{ text: 'Planli', value: 'scheduled' }, { text: 'Devam Ediyor', value: 'in_progress' }, { text: 'Tamamlandi', value: 'completed' }, { text: 'Iptal Edildi', value: 'cancelled' }], onFilter: (value, record) => record.status === value },
    { title: 'Islemler', key: 'actions', width: 120, render: (_, record) => (
      <Space>
        <Tooltip title="Duzenle"><Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)} /></Tooltip>
        <Popconfirm title="Vardiyayi silmek istediginize emin misiniz?" onConfirm={() => handleDelete(record.id)} okText="Evet" cancelText="Hayir">
          <Tooltip title="Sil"><Button type="text" danger icon={<DeleteOutlined />} /></Tooltip>
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
        {dayShifts.length > 3 && <li><Text type="secondary" style={{ fontSize: 10 }}>+{dayShifts.length - 3} daha</Text></li>}
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
            <Title level={4} style={{ margin: 0 }}>Vardiya Yonetimi</Title>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchData}>Yenile</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Yeni Vardiya</Button>
            </Space>
          </div>

          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Toplam Vardiya" value={pagination.total} prefix={<CalendarOutlined />} /></Card></Col>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Bugunun Vardiyelari" value={todayShifts.length} prefix={<TeamOutlined />} valueStyle={{ color: '#1890ff' }} /></Card></Col>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Planli" value={scheduledShifts.length} prefix={<ClockCircleOutlined />} valueStyle={{ color: '#faad14' }} /></Card></Col>
            <Col xs={24} sm={6}><Card size="small"><Statistic title="Toplam Saat" value={totalHours.toFixed(1)} suffix="saat" valueStyle={{ color: '#52c41a' }} /></Card></Col>
          </Row>

          {conflicts.length > 0 && (
            <Alert message={`${conflicts.length} Vardiya Catismasi Tespit Edildi`} description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {conflicts.slice(0, 3).map((conflict, index) => (<li key={index}><Tag color={conflict.type === 'overtime' ? 'orange' : 'red'}>{conflict.type.toUpperCase()}</Tag>{conflict.message}</li>))}
                {conflicts.length > 3 && <li>...ve {conflicts.length - 3} daha</li>}
              </ul>
            } type="warning" showIcon icon={<WarningOutlined />} style={{ marginBottom: 24 }} />
          )}

          <Card bordered={false} style={{ marginBottom: 24 }}>
            <Row gutter={16} align="middle">
              <Col xs={24} sm={8}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Tarih Araligi</Text>
                <RangePicker value={dateRange} onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])} style={{ width: '100%' }} />
              </Col>
              <Col xs={24} sm={8}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Departman</Text>
                <Select placeholder="Tum departmanlar" style={{ width: '100%' }} value={selectedDepartment} onChange={setSelectedDepartment} allowClear>
                  {departments.map((dept) => (<Option key={dept.id} value={dept.id}>{dept.name}</Option>))}
                </Select>
              </Col>
              <Col xs={24} sm={8}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Gorunum</Text>
                <Tabs activeKey={viewMode} onChange={(key) => setViewMode(key as 'list' | 'calendar')} items={[
                  { key: 'list', label: <><UnorderedListOutlined /> Liste</> },
                  { key: 'calendar', label: <><CalendarOutlined /> Takvim</> },
                ]} />
              </Col>
            </Row>
          </Card>

          <Card bordered={false}>
            {viewMode === 'list' ? (
              <Table columns={columns} dataSource={shifts} rowKey="id" pagination={{
                current: pagination.page, pageSize: pagination.pageSize, total: pagination.total,
                showSizeChanger: true, showTotal: (total) => `Toplam ${total} vardiya`,
                onChange: (page, pageSize) => setPagination({ ...pagination, page, pageSize }),
              }} />
            ) : (
              <Calendar dateCellRender={dateCellRender} />
            )}
          </Card>

          <Modal title={editingShift ? 'Vardiya Duzenle' : 'Yeni Vardiya Olustur'} open={isModalOpen} onCancel={() => { setIsModalOpen(false); form.resetFields(); }} footer={null} width={600}>
            <Form form={form} layout="vertical" onFinish={handleSubmit}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="employee_id" label="Calisan" rules={[{ required: true, message: 'Calisan secin' }]}>
                    <Select placeholder="Calisan secin" showSearch optionFilterProp="children">
                      {employees.map((emp) => (<Option key={emp.id} value={emp.id}>{emp.name} - {emp.department_name}</Option>))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="department_id" label="Departman" rules={[{ required: true, message: 'Departman secin' }]}>
                    <Select placeholder="Departman secin">{departments.map((dept) => (<Option key={dept.id} value={dept.id}>{dept.name}</Option>))}</Select>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="date" label="Tarih" rules={[{ required: true, message: 'Tarih secin' }]}>
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="time_range" label="Saat Araligi" rules={[{ required: true, message: 'Saat araligi secin' }]}>
                    <TimePicker.RangePicker format="HH:mm" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              {editingShift && (
                <Form.Item name="status" label="Durum">
                  <Select>
                    <Option value="scheduled">Planli</Option>
                    <Option value="in_progress">Devam Ediyor</Option>
                    <Option value="completed">Tamamlandi</Option>
                    <Option value="cancelled">Iptal Edildi</Option>
                  </Select>
                </Form.Item>
              )}
              <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                <Space>
                  <Button onClick={() => setIsModalOpen(false)}>Iptal</Button>
                  <Button type="primary" htmlType="submit">{editingShift ? 'Guncelle' : 'Olustur'}</Button>
                </Space>
              </Form.Item>
            </Form>
          </Modal>
        </div>
      </Spin>
    </DashboardLayout>
  );
}
