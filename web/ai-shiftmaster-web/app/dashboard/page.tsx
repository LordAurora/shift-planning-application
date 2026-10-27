'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Card, Col, Empty, Row, Select, Space, Spin, Statistic, Table, Tag, Tooltip, Typography, message } from 'antd';
import {
  ApartmentOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  FileExcelOutlined,
  ReloadOutlined,
  RobotOutlined,
  TeamOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts';
import dayjs, { Dayjs } from 'dayjs';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import DashboardLayout from '../components/DashboardLayout';
import { dashboardService, DashboardSummary } from '../lib/services';

const { Title, Text } = Typography;

const DEPT_COLORS = ['#1e3a5f', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#14b8a6', '#ef4444'];
const SHIFT_COLORS: Record<string, string> = { Morning: '#f59e0b', Day: '#22c55e', Evening: '#3b82f6', Night: '#6366f1' };

type RangeKey = 'this_week' | 'next_week' | 'this_month' | 'next_month';

const RANGES: Record<RangeKey, { label: string; get: () => [Dayjs, Dayjs] }> = {
  this_week: { label: 'This week', get: () => [dayjs().day(1).startOf('day'), dayjs().day(1).add(6, 'day')] },
  next_week: { label: 'Next week', get: () => [dayjs().day(1).add(7, 'day'), dayjs().day(1).add(13, 'day')] },
  this_month: { label: 'This month', get: () => [dayjs().startOf('month'), dayjs().endOf('month')] },
  next_month: { label: 'Next month', get: () => [dayjs().add(1, 'month').startOf('month'), dayjs().add(1, 'month').endOf('month')] },
};

const kpiCard = (background: string) => ({ background, border: 'none' });

export default function DashboardPage() {
  const router = useRouter();
  const [range, setRange] = useState<RangeKey>('this_week');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardSummary | null>(null);

  const load = async () => {
    setLoading(true);
    const [start, end] = RANGES[range].get();
    try {
      setData(await dashboardService.getSummary({ start_date: start.format('YYYY-MM-DD'), end_date: end.format('YYYY-MM-DD') }));
    } catch {
      message.error('Could not load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  const exportReport = () => {
    if (!data) return;
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet([
      { Metric: 'Period', Value: `${data.period.start_date} – ${data.period.end_date}` },
      { Metric: 'Employees', Value: data.total_employees },
      { Metric: 'Shifts', Value: data.total_shifts },
      { Metric: 'Planned hours', Value: data.total_hours },
      { Metric: 'Employees scheduled', Value: data.employees_scheduled },
      { Metric: 'Above contract hours', Value: data.over_contract },
    ]), 'Summary');
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(data.by_weekday), 'By weekday');
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(data.departments.map((d) => ({ Department: d.name, Employees: d.value }))), 'Departments');
    const buffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    saveAs(new Blob([buffer], { type: 'application/octet-stream' }), `Dashboard_${dayjs().format('YYYY-MM-DD')}.xlsx`);
  };

  const periodLabel = data
    ? `${dayjs(data.period.start_date).format('MMM D')} – ${dayjs(data.period.end_date).format('MMM D, YYYY')}`
    : '';
  const hasShifts = (data?.total_shifts ?? 0) > 0;
  const shiftTypes = (data?.shift_types ?? []).filter((t) => t.value > 0);

  return (
    <DashboardLayout>
      <Spin spinning={loading}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>Dashboard</Title>
            <Text type="secondary">{periodLabel}</Text>
          </div>
          <Space wrap>
            <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
            <Select
              value={range}
              onChange={setRange}
              style={{ width: 150 }}
              options={(Object.keys(RANGES) as RangeKey[]).map((k) => ({ value: k, label: RANGES[k].label }))}
            />
            <Tooltip title="Download this report as Excel">
              <Button icon={<FileExcelOutlined />} onClick={exportReport} disabled={!data}>Export</Button>
            </Tooltip>
          </Space>
        </div>

        <Row gutter={[16, 16]}>
          {[
            { title: 'Employees', value: data?.total_employees ?? 0, icon: <TeamOutlined />, bg: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%)' },
            { title: 'Shifts in period', value: data?.total_shifts ?? 0, icon: <CalendarOutlined />, bg: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)' },
            { title: 'Planned hours', value: data?.total_hours ?? 0, icon: <ClockCircleOutlined />, bg: 'linear-gradient(135deg, #16a34a 0%, #4ade80 100%)', suffix: 'h' },
            { title: 'Above contract hours', value: data?.over_contract ?? 0, icon: <WarningOutlined />, bg: 'linear-gradient(135deg, #ea580c 0%, #fb923c 100%)' },
          ].map((k) => (
            <Col xs={24} sm={12} lg={6} key={k.title}>
              <Card style={kpiCard(k.bg)}>
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>{k.title}</span>}
                  value={k.value}
                  suffix={k.suffix}
                  prefix={React.cloneElement(k.icon, { style: { color: '#fff' } })}
                  styles={{ content: { color: '#fff' } }}
                />
              </Card>
            </Col>
          ))}
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={16}>
            <Card title="Shifts by weekday" variant="borderless" extra={<Tag color="blue">{RANGES[range].label}</Tag>}>
              {hasShifts ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data?.by_weekday}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="shifts" name="Shifts" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="employees" name="People working" fill="#7dd3fc" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Empty style={{ height: 300, paddingTop: 80 }} description="No shifts planned in this period">
                  <Button type="primary" icon={<RobotOutlined />} onClick={() => router.push('/ai-optimization')}>Generate a schedule</Button>
                </Empty>
              )}
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="Employees by department" variant="borderless">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={data?.departments ?? []} cx="50%" cy="45%" innerRadius={60} outerRadius={95} paddingAngle={3} dataKey="value">
                    {(data?.departments ?? []).map((_, i) => <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />)}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={14}>
            <Card title="Six-month trend" variant="borderless">
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={data?.monthly_trend ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" />
                  <YAxis allowDecimals={false} />
                  <RechartsTooltip />
                  <Legend />
                  <Area type="monotone" dataKey="scheduled" name="Scheduled" stroke="#1e3a5f" fill="#1e3a5f" fillOpacity={0.25} />
                  <Area type="monotone" dataKey="completed" name="Completed" stroke="#22c55e" fill="#22c55e" fillOpacity={0.25} />
                  <Area type="monotone" dataKey="cancelled" name="Cancelled" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title="Shift type mix" variant="borderless">
              {shiftTypes.length ? (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={shiftTypes} cx="50%" cy="45%" innerRadius={50} outerRadius={90} paddingAngle={3} dataKey="value">
                      {shiftTypes.map((t) => <Cell key={t.name} fill={SHIFT_COLORS[t.name]} />)}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Empty style={{ height: 260, paddingTop: 70 }} description="No shifts in this period" />
              )}
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={16}>
            <Card title="Upcoming shifts" variant="borderless">
              <Table
                size="small"
                rowKey="id"
                pagination={false}
                dataSource={data?.upcoming_shifts ?? []}
                locale={{ emptyText: 'No upcoming shifts in this period' }}
                scroll={{ x: 520 }}
                columns={[
                  { title: 'Employee', dataIndex: 'employee', key: 'employee' },
                  { title: 'Department', dataIndex: 'department', key: 'department' },
                  { title: 'Date', dataIndex: 'start_time', key: 'date', render: (v: string) => dayjs(v).format('ddd, MMM D') },
                  { title: 'Time', key: 'time', render: (_: unknown, r: { start_time: string; end_time: string }) => `${dayjs(r.start_time).format('HH:mm')} – ${dayjs(r.end_time).format('HH:mm')}` },
                  { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : 'blue'}>{s}</Tag> },
                ]}
              />
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="Quick actions" variant="borderless">
              {[
                { href: '/ai-optimization', title: 'AI schedule optimization', text: 'Generate an optimized plan', icon: <RobotOutlined />, bg: '#1e3a5f' },
                { href: '/employees', title: 'Employees', text: 'Limits, availability and roles', icon: <TeamOutlined />, bg: '#3b82f6' },
                { href: '/shifts', title: 'Shift calendar', text: 'Weekly and monthly views', icon: <CalendarOutlined />, bg: '#16a34a' },
                { href: '/rules', title: 'Shift rules', text: `${data?.total_departments ?? 0} departments`, icon: <ApartmentOutlined />, bg: '#8b5cf6' },
              ].map((a) => (
                <div
                  key={a.href}
                  onClick={() => router.push(a.href)}
                  className="quick-action"
                  style={{ background: a.bg }}
                >
                  <span className="quick-action-icon">{a.icon}</span>
                  <div>
                    <Text strong style={{ color: '#fff' }}>{a.title}</Text>
                    <br />
                    <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>{a.text}</Text>
                  </div>
                </div>
              ))}
            </Card>
          </Col>
        </Row>
      </Spin>
    </DashboardLayout>
  );
}
