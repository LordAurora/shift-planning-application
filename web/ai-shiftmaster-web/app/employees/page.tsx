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
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

const DAYS_OF_WEEK = [
  { value: 0, label: 'Pazar' },
  { value: 1, label: 'Pazartesi' },
  { value: 2, label: 'Sali' },
  { value: 3, label: 'Carsamba' },
  { value: 4, label: 'Persembe' },
  { value: 5, label: 'Cuma' },
  { value: 6, label: 'Cumartesi' },
];

const ROLES = ['Gelistirici', 'Yonetici', 'Analist', 'Tasarimci', 'Destek', 'Muhendis', 'Operasyon'];

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
    message.success('Rastgele sifre olusturuldu!');
  };

  const copyPassword = () => {
    const password = form.getFieldValue('password');
    if (password) {
      navigator.clipboard.writeText(password);
      message.success('Sifre panoya kopyalandi!');
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
      message.error('Calisanlar yuklenirken hata olustu');
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getAll();
      setDepartments(response);
    } catch (error) {
      message.error('Departmanlar yuklenirken hata olustu');
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
      message.success('Calisan basariyla silindi');
      fetchEmployees();
    } catch (error) {
      message.error('Calisan silinirken hata olustu');
    }
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    try {
      const availability: AvailabilitySlot[] = (values.availability_days as number[]).map(day => ({
        day,
        start_time: (values.availability_start as dayjs.Dayjs).format('HH:mm'),
        end_time: (values.availability_end as dayjs.Dayjs).format('HH:mm'),
      }));

      const employeeData: any = {
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
          employeeData.password = values.password;
        }
        await employeeService.update(editingEmployee.id, employeeData);
        message.success('Calisan basariyla guncellendi');
      } else {
        // Password is required for new employees
        employeeData.password = values.password;
        await employeeService.create(employeeData);
        message.success('Calisan basariyla olusturuldu');
      }
      setModalVisible(false);
      form.resetFields();
      fetchEmployees();
    } catch (error: any) {
      message.error(error?.response?.data?.detail || 'Calisan kaydedilirken hata olustu');
    }
  };

  const columns: ColumnsType<Employee> = [
    {
      title: 'Ad Soyad',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'E-posta',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Pozisyon',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => <Tag color="blue">{role}</Tag>,
    },
    {
      title: 'Departman',
      dataIndex: 'department_name',
      key: 'department_name',
    },
    {
      title: 'Haftalik Limit',
      dataIndex: 'weekly_working_limit',
      key: 'weekly_working_limit',
      render: (hours: number) => `${hours}s`,
    },
    {
      title: 'Fazla Mesai Limit',
      dataIndex: 'overtime_limit',
      key: 'overtime_limit',
      render: (hours: number) => `${hours}s`,
    },
    {
      title: 'Musait Gunler',
      dataIndex: 'availability',
      key: 'availability',
      render: (availability: AvailabilitySlot[]) => (
        <span>
          {availability?.map(a => DAYS_OF_WEEK.find(d => d.value === a.day)?.label.slice(0, 3)).join(', ') || '-'}
        </span>
      ),
    },
    {
      title: 'Islemler',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Duzenle">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Calisani Sil"
            description="Bu calisani silmek istediginizden emin misiniz? Kullanici hesabi da silinecektir."
            onConfirm={() => handleDelete(record.id)}
            okText="Evet"
            cancelText="Hayir"
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
            Calisan Yonetimi
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Calisan Ekle
          </Button>
        </div>

        <Card bordered={false} style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="Ad veya e-posta ile ara..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Select
                placeholder="Departmana gore filtrele"
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
                Yenile
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
                showTotal: (total) => `Toplam ${total} calisan`,
                onChange: (page, pageSize) => setPagination(prev => ({ ...prev, current: page, pageSize })),
              }}
            />
          </Spin>
        </Card>

        <Modal
          title={editingEmployee ? 'Calisani Duzenle' : 'Yeni Calisan Ekle'}
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
                  label="Ad Soyad"
                  rules={[{ required: true, message: 'Lutfen ad soyad girin' }]}
                >
                  <Input placeholder="Ornek: Ahmet Yilmaz" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="email"
                  label="E-posta (Giris icin kullanilacak)"
                  rules={[
                    { required: true, message: 'Lutfen e-posta girin' },
                    { type: 'email', message: 'Gecerli bir e-posta girin' },
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
                  <span>{editingEmployee ? 'Yeni Sifre (Degistirmek icin doldurun)' : 'Sifre (Mobil giris icin)'}</span>
                  <Tooltip title="Calisan bu sifre ile mobil uygulamadan giris yapacak">
                    <KeyOutlined style={{ color: '#1e3a5f' }} />
                  </Tooltip>
                </Space>
              }
              rules={editingEmployee ? [] : [
                { required: true, message: 'Lutfen sifre girin' },
                { min: 6, message: 'Sifre en az 6 karakter olmali' },
              ]}
            >
              <Input.Group compact style={{ display: 'flex' }}>
                <Input
                  style={{ flex: 1 }}
                  type={showPassword ? 'text' : 'password'}
                  placeholder={editingEmployee ? 'Yeni sifre (opsiyonel)' : 'Sifre girin veya olusturun'}
                  value={form.getFieldValue('password')}
                  onChange={(e) => form.setFieldValue('password', e.target.value)}
                  suffix={
                    <Space>
                      <Tooltip title={showPassword ? 'Sifreyi gizle' : 'Sifreyi goster'}>
                        <Button
                          type="text"
                          size="small"
                          icon={showPassword ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                          onClick={() => setShowPassword(!showPassword)}
                        />
                      </Tooltip>
                      <Tooltip title="Sifreyi kopyala">
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
                <Tooltip title="Rastgele guclu sifre olustur">
                  <Button
                    type="primary"
                    icon={<KeyOutlined />}
                    onClick={generatePassword}
                    style={{ backgroundColor: '#22c55e', borderColor: '#22c55e' }}
                  >
                    Olustur
                  </Button>
                </Tooltip>
              </Input.Group>
            </Form.Item>
            {generatedPassword && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f0fdf4', borderRadius: 8, border: '1px solid #22c55e' }}>
                <Text type="secondary">Olusturulan sifre: </Text>
                <Text strong copyable style={{ color: '#22c55e' }}>{generatedPassword}</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>Bu sifreyi calisana iletin. Mobil uygulamadan giris icin kullanacak.</Text>
              </div>
            )}

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="role"
                  label="Pozisyon"
                  rules={[{ required: true, message: 'Lutfen pozisyon secin' }]}
                >
                  <Select placeholder="Pozisyon secin">
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
                  label="Departman"
                  rules={[{ required: true, message: 'Lutfen departman secin' }]}
                >
                  <Select placeholder="Departman secin">
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
                  label="Haftalik Calisma Limiti (saat)"
                  rules={[{ required: true, message: 'Lutfen haftalik limit girin' }]}
                >
                  <InputNumber min={0} max={168} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="overtime_limit"
                  label="Fazla Mesai Limiti (saat)"
                  rules={[{ required: true, message: 'Lutfen fazla mesai limiti girin' }]}
                >
                  <InputNumber min={0} max={40} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="availability_days"
              label="Musait Gunler"
              rules={[{ required: true, message: 'Lutfen musait gunleri secin' }]}
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
                  label="Musaitlik Baslangic Saati"
                  rules={[{ required: true, message: 'Lutfen baslangic saati secin' }]}
                >
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="availability_end"
                  label="Musaitlik Bitis Saati"
                  rules={[{ required: true, message: 'Lutfen bitis saati secin' }]}
                >
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
              <Space style={{ float: 'right' }}>
                <Button onClick={() => setModalVisible(false)}>Iptal</Button>
                <Button type="primary" htmlType="submit">
                  {editingEmployee ? 'Guncelle' : 'Olustur'}
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
