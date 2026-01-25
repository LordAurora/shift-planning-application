'use client';

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Table, Tag, Select, Space, Button, Tooltip, Spin, message } from 'antd';
import {
  TeamOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  RiseOutlined,
  FallOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import DashboardLayout from '../components/DashboardLayout';
import { employeeService, departmentService, shiftService } from '../lib/services';
import dayjs from 'dayjs';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

const { Title, Text } = Typography;

interface DashboardStats {
  totalEmployees: number;
  totalShifts: number;
  totalHours: number;
  conflicts: number;
  departments: { name: string; value: number; color: string }[];
}

const COLORS = ['#1e3a5f', '#4a6fa5', '#7dd3fc', '#94a3b8', '#cbd5e1', '#22c55e', '#f59e0b'];

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<string>('week');
  const [stats, setStats] = useState<DashboardStats>({
    totalEmployees: 0,
    totalShifts: 0,
    totalHours: 0,
    conflicts: 0,
    departments: [],
  });
  const [recentShifts, setRecentShifts] = useState<any[]>([]);
  const [departmentData, setDepartmentData] = useState<any[]>([]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch employees
      const employeesRes = await employeeService.getAll({ page: 1, page_size: 100 });
      const totalEmployees = employeesRes.total;

      // Fetch departments
      const departments = await departmentService.getAll();
      
      // Count employees per department
      const deptCounts: { [key: string]: number } = {};
      employeesRes.items.forEach(emp => {
        const deptName = emp.department_name || 'Bilinmiyor';
        deptCounts[deptName] = (deptCounts[deptName] || 0) + 1;
      });

      const deptData = Object.entries(deptCounts).map(([name, value], index) => ({
        name,
        value,
        color: COLORS[index % COLORS.length],
      }));
      setDepartmentData(deptData);

      // Fetch shifts for current week
      const today = dayjs();
      const startOfWeek = today.startOf('week');
      const endOfWeek = today.endOf('week');
      
      let shiftsData: any[] = [];
      try {
        const shiftsRes = await shiftService.getAll({
          page: 1,
          page_size: 50,
          start_date: startOfWeek.format('YYYY-MM-DD'),
          end_date: endOfWeek.format('YYYY-MM-DD'),
        });
        shiftsData = shiftsRes.items || [];
      } catch (e) {
        // If shifts endpoint fails, use empty array
        shiftsData = [];
      }

      // Calculate total hours
      let totalHours = 0;
      shiftsData.forEach(shift => {
        const start = dayjs(shift.start_time);
        const end = dayjs(shift.end_time);
        totalHours += end.diff(start, 'hour', true);
      });

      // Format shifts for table
      const formattedShifts = shiftsData.slice(0, 5).map((shift, index) => ({
        key: shift.id || index,
        employee: shift.employee_name || 'Bilinmiyor',
        department: shift.department_name || 'Bilinmiyor',
        shift: `${dayjs(shift.start_time).format('HH:mm')} - ${dayjs(shift.end_time).format('HH:mm')}`,
        date: dayjs(shift.start_time).format('YYYY-MM-DD'),
        status: shift.status || 'scheduled',
        hours: Math.round(dayjs(shift.end_time).diff(dayjs(shift.start_time), 'hour', true)),
      }));
      setRecentShifts(formattedShifts);

      setStats({
        totalEmployees,
        totalShifts: shiftsData.length,
        totalHours: Math.round(totalHours),
        conflicts: 0,
        departments: deptData,
      });

    } catch (error) {
      console.error('Dashboard verisi yuklenirken hata:', error);
      message.error('Dashboard verisi yuklenirken hata olustu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  // Mock data for charts (will be replaced with real data when API is ready)
  const weeklyShiftData = [
    { name: 'Pzt', shifts: Math.floor(stats.totalShifts / 5), hours: Math.floor(stats.totalHours / 5), employees: Math.floor(stats.totalEmployees * 0.8) },
    { name: 'Sal', shifts: Math.floor(stats.totalShifts / 5) + 2, hours: Math.floor(stats.totalHours / 5) + 16, employees: Math.floor(stats.totalEmployees * 0.85) },
    { name: 'Car', shifts: Math.floor(stats.totalShifts / 5) + 1, hours: Math.floor(stats.totalHours / 5) + 8, employees: Math.floor(stats.totalEmployees * 0.82) },
    { name: 'Per', shifts: Math.floor(stats.totalShifts / 5) + 3, hours: Math.floor(stats.totalHours / 5) + 24, employees: Math.floor(stats.totalEmployees * 0.9) },
    { name: 'Cum', shifts: Math.floor(stats.totalShifts / 5) + 4, hours: Math.floor(stats.totalHours / 5) + 32, employees: Math.floor(stats.totalEmployees * 0.95) },
    { name: 'Cmt', shifts: Math.floor(stats.totalShifts / 7), hours: Math.floor(stats.totalHours / 7), employees: Math.floor(stats.totalEmployees * 0.4) },
    { name: 'Paz', shifts: Math.floor(stats.totalShifts / 10), hours: Math.floor(stats.totalHours / 10), employees: Math.floor(stats.totalEmployees * 0.3) },
  ];

  const shiftTypeData = [
    { name: 'Sabah (06-14)', value: 45, color: '#fbbf24' },
    { name: 'Gunduz (09-17)', value: 35, color: '#22c55e' },
    { name: 'Aksam (14-22)', value: 15, color: '#3b82f6' },
    { name: 'Gece (22-06)', value: 5, color: '#6366f1' },
  ];

  const monthlyTrendData = [
    { month: 'Oca', planned: Math.floor(stats.totalShifts * 4.2), completed: Math.floor(stats.totalShifts * 4), overtime: Math.floor(stats.totalShifts * 0.4) },
    { month: 'Sub', planned: Math.floor(stats.totalShifts * 4), completed: Math.floor(stats.totalShifts * 3.9), overtime: Math.floor(stats.totalShifts * 0.3) },
    { month: 'Mar', planned: Math.floor(stats.totalShifts * 4.5), completed: Math.floor(stats.totalShifts * 4.4), overtime: Math.floor(stats.totalShifts * 0.5) },
    { month: 'Nis', planned: Math.floor(stats.totalShifts * 4.3), completed: Math.floor(stats.totalShifts * 4.2), overtime: Math.floor(stats.totalShifts * 0.35) },
    { month: 'May', planned: Math.floor(stats.totalShifts * 4.8), completed: Math.floor(stats.totalShifts * 4.7), overtime: Math.floor(stats.totalShifts * 0.6) },
    { month: 'Haz', planned: Math.floor(stats.totalShifts * 4.6), completed: Math.floor(stats.totalShifts * 4.5), overtime: Math.floor(stats.totalShifts * 0.45) },
  ];

  const columns = [
    { title: 'Calisan', dataIndex: 'employee', key: 'employee' },
    { title: 'Departman', dataIndex: 'department', key: 'department' },
    { title: 'Vardiya', dataIndex: 'shift', key: 'shift' },
    { title: 'Tarih', dataIndex: 'date', key: 'date' },
    { title: 'Saat', dataIndex: 'hours', key: 'hours', render: (hours: number) => `${hours}s` },
    {
      title: 'Durum',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
          active: { color: 'green', text: 'AKTIF', icon: <SyncOutlined spin /> },
          completed: { color: 'blue', text: 'TAMAMLANDI', icon: <CheckCircleOutlined /> },
          scheduled: { color: 'orange', text: 'PLANLI', icon: <CalendarOutlined /> },
        };
        const config = statusConfig[status] || statusConfig.scheduled;
        return <Tag color={config.color} icon={config.icon}>{config.text}</Tag>;
      },
    },
  ];

  const exportDashboardData = () => {
    const workbook = XLSX.utils.book_new();
    const weeklyWs = XLSX.utils.json_to_sheet(weeklyShiftData);
    XLSX.utils.book_append_sheet(workbook, weeklyWs, 'Haftalik Vardiyalar');
    const shiftsWs = XLSX.utils.json_to_sheet(recentShifts);
    XLSX.utils.book_append_sheet(workbook, shiftsWs, 'Son Vardiyalar');
    const deptWs = XLSX.utils.json_to_sheet(departmentData.map(d => ({ Departman: d.name, Calisan: d.value })));
    XLSX.utils.book_append_sheet(workbook, deptWs, 'Departman Dagilimi');
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const data = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(data, `Dashboard_Raporu_${dayjs().format('YYYY-MM-DD')}.xlsx`);
  };

  return (
    <DashboardLayout>
      <Spin spinning={loading} tip="Veriler yukleniyor...">
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <Title level={4} style={{ margin: 0 }}>Dashboard</Title>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchDashboardData}>Yenile</Button>
              <Select value={timeRange} onChange={setTimeRange} style={{ width: 150 }} options={[
                { value: 'today', label: 'Bugun' },
                { value: 'week', label: 'Bu Hafta' },
                { value: 'month', label: 'Bu Ay' },
                { value: 'quarter', label: 'Bu Ceyrek' },
              ]} />
              <Tooltip title="Raporu Excel olarak indir">
                <Button icon={<FileExcelOutlined />} onClick={exportDashboardData}>Excel Indir</Button>
              </Tooltip>
            </Space>
          </div>

          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false} style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)' }}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>Toplam Calisan</span>} 
                  value={stats.totalEmployees} 
                  prefix={<TeamOutlined style={{ color: '#fff' }} />} 
                  valueStyle={{ color: '#fff' }} 
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false} style={{ background: 'linear-gradient(135deg, #4a6fa5 0%, #6b8cbe 100%)' }}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>Bu Hafta Vardiya</span>} 
                  value={stats.totalShifts} 
                  prefix={<CalendarOutlined style={{ color: '#fff' }} />} 
                  valueStyle={{ color: '#fff' }} 
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false} style={{ background: 'linear-gradient(135deg, #22c55e 0%, #4ade80 100%)' }}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>Planlanan Saat</span>} 
                  value={stats.totalHours} 
                  prefix={<ClockCircleOutlined style={{ color: '#fff' }} />} 
                  valueStyle={{ color: '#fff' }} 
                  suffix="s" 
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card bordered={false} style={{ background: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)' }}>
                <Statistic 
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>Departman Sayisi</span>} 
                  value={departmentData.length} 
                  prefix={<WarningOutlined style={{ color: '#fff' }} />} 
                  valueStyle={{ color: '#fff' }} 
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={16}>
              <Card title="Haftalik Vardiya Dagilimi" bordered={false} extra={<Tag color="blue">Son 7 Gun</Tag>}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={weeklyShiftData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }} />
                    <Legend />
                    <Bar dataKey="shifts" name="Vardiya Sayisi" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="employees" name="Calisan Sayisi" fill="#7dd3fc" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="Departman Dagilimi" bordered={false}>
                {departmentData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie 
                        data={departmentData} 
                        cx="50%" 
                        cy="50%" 
                        innerRadius={60} 
                        outerRadius={100} 
                        paddingAngle={2} 
                        dataKey="value" 
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} 
                        labelLine={false}
                      >
                        {departmentData.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.color} />))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ textAlign: 'center', padding: 60 }}>
                    <Text type="secondary">Henuz departman verisi yok</Text>
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} lg={12}>
              <Card title="Aylik Trend Analizi" bordered={false}>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={monthlyTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <RechartsTooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }} />
                    <Legend />
                    <Area type="monotone" dataKey="planned" name="Planlanan" stroke="#1e3a5f" fill="#1e3a5f" fillOpacity={0.3} />
                    <Area type="monotone" dataKey="completed" name="Tamamlanan" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} />
                    <Area type="monotone" dataKey="overtime" name="Fazla Mesai" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Vardiya Tipi Dagilimi" bordered={false}>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={shiftTypeData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, value }) => `${name}: ${value}%`}>
                      {shiftTypeData.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.color} />))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          <Card title="Son Vardiyalar" bordered={false} style={{ marginTop: 16 }} extra={
            <Space>
              <Button size="small" icon={<DownloadOutlined />} onClick={() => {
                const ws = XLSX.utils.json_to_sheet(recentShifts);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Vardiyalar');
                const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
                const data = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                saveAs(data, `Vardiyalar_${dayjs().format('YYYY-MM-DD')}.xlsx`);
              }}>Excel</Button>
              <a href="/shifts">Tumunu Gor</a>
            </Space>
          }>
            {recentShifts.length > 0 ? (
              <Table columns={columns} dataSource={recentShifts} pagination={false} size="middle" />
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Text type="secondary">Henuz vardiya verisi yok</Text>
              </div>
            )}
          </Card>

          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col xs={24}>
              <Card title="Hizli Islemler" bordered={false}>
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={8}>
                    <a href="/ai-optimization" style={{ display: 'block', padding: 20, background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)', borderRadius: 12, textAlign: 'center' }}>
                      <div style={{ fontSize: 32, marginBottom: 8 }}></div>
                      <Text strong style={{ color: '#fff', fontSize: 16 }}>AI Vardiya Optimizasyonu</Text>
                      <br />
                      <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>Otomatik optimal vardiya plani olusturun</Text>
                    </a>
                  </Col>
                  <Col xs={24} sm={8}>
                    <a href="/employees" style={{ display: 'block', padding: 20, background: 'linear-gradient(135deg, #4a6fa5 0%, #6b8cbe 100%)', borderRadius: 12, textAlign: 'center' }}>
                      <div style={{ fontSize: 32, marginBottom: 8 }}></div>
                      <Text strong style={{ color: '#fff', fontSize: 16 }}>Calisan Yonetimi</Text>
                      <br />
                      <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>Calisan bilgilerini duzenleyin</Text>
                    </a>
                  </Col>
                  <Col xs={24} sm={8}>
                    <a href="/shifts" style={{ display: 'block', padding: 20, background: 'linear-gradient(135deg, #22c55e 0%, #4ade80 100%)', borderRadius: 12, textAlign: 'center' }}>
                      <div style={{ fontSize: 32, marginBottom: 8 }}></div>
                      <Text strong style={{ color: '#fff', fontSize: 16 }}>Vardiya Takvimi</Text>
                      <br />
                      <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>Haftalik ve aylik vardiya gorunumu</Text>
                    </a>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </div>
      </Spin>
    </DashboardLayout>
  );
}
