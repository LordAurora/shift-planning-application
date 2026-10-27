'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Badge,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Divider,
  Dropdown,
  InputNumber,
  Modal,
  Progress,
  Result,
  Row,
  Select,
  Slider,
  Space,
  Spin,
  Statistic,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CopyOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  FilterOutlined,
  HeartOutlined,
  HomeOutlined,
  PrinterOutlined,
  ReloadOutlined,
  RobotOutlined,
  SaveOutlined,
  SettingOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  WarningOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { MenuProps } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import DashboardLayout from '../components/DashboardLayout';
import { aiService, departmentService, employeeService } from '../lib/services';
import type {
  Department,
  Employee,
  OptimizationResult,
  OptimizationSettings,
  OptimizedShift,
  ShiftTypeKey,
} from '../types';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

const SHIFT_TYPES: { key: ShiftTypeKey; label: string; time: string; color: string }[] = [
  { key: 'morning', label: 'Morning', time: '06:00 – 14:00', color: 'gold' },
  { key: 'day', label: 'Day', time: '09:00 – 17:00', color: 'green' },
  { key: 'afternoon', label: 'Evening', time: '14:00 – 22:00', color: 'blue' },
  { key: 'night', label: 'Night', time: '22:00 – 06:00', color: 'purple' },
];
const SHIFT_LOOKUP = Object.fromEntries(SHIFT_TYPES.map((s) => [s.key, s]));

const WEEK_DAYS = [
  { key: 'monday', label: 'Monday' },
  { key: 'tuesday', label: 'Tuesday' },
  { key: 'wednesday', label: 'Wednesday' },
  { key: 'thursday', label: 'Thursday' },
  { key: 'friday', label: 'Friday' },
  { key: 'saturday', label: 'Saturday' },
  { key: 'sunday', label: 'Sunday' },
];

const DEFAULT_SETTINGS: OptimizationSettings = {
  shift_types: ['morning', 'day', 'afternoon'],
  operating_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
  is_24_7: false,
  min_employees_per_shift: 2,
  max_employees_per_shift: 10,
  max_hours_per_week: 45,
  max_consecutive_days: 5,
  min_rest_hours: 11,
  allow_overtime: false,
  consider_preferences: true,
  preference_weight: 70,
  balance_workload: true,
};

const scoreColor = (value: number) => (value >= 85 ? '#16a34a' : value >= 70 ? '#d97706' : '#dc2626');

export default function AIOptimizationPage() {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>([
    dayjs().add(1, 'week').startOf('week').add(1, 'day'),
    dayjs().add(1, 'week').startOf('week').add(7, 'day'),
  ]);
  const [selectedDepartments, setSelectedDepartments] = useState<number[]>([]);
  const [settings, setSettings] = useState<OptimizationSettings>(DEFAULT_SETTINGS);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [dataLoading, setDataLoading] = useState(true);

  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [shiftFilter, setShiftFilter] = useState<ShiftTypeKey | 'all'>('all');

  const fetchData = async () => {
    setDataLoading(true);
    try {
      const [empResponse, deptResponse] = await Promise.all([
        employeeService.getAll({ page: 1, page_size: 500 }),
        departmentService.getAll(),
      ]);
      setEmployees(empResponse.items);
      setDepartments(deptResponse);
    } catch {
      message.error('Could not load employees and departments.');
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const update = <K extends keyof OptimizationSettings>(key: K, value: OptimizationSettings[K]) =>
    setSettings((prev) => ({ ...prev, [key]: value }));

  const scopedEmployees = useMemo(
    () =>
      selectedDepartments.length
        ? employees.filter((e) => selectedDepartments.includes(e.department_id))
        : employees,
    [employees, selectedDepartments]
  );
  const withPreferences = scopedEmployees.filter((e) => e.preferences?.preferred_shift).length;

  const handleOptimize = async () => {
    if (!dateRange) {
      message.warning('Select a date range first.');
      return;
    }
    if (!settings.shift_types.length) {
      message.warning('Enable at least one shift type.');
      return;
    }
    setRunning(true);
    setResult(null);
    try {
      const response = await aiService.optimize({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        department_ids: selectedDepartments.length ? selectedDepartments : undefined,
        settings,
      });
      setResult(response);
      setShiftFilter('all');
      message.success(response.message);
    } catch {
      message.error('Optimization failed. Please try again.');
    } finally {
      setRunning(false);
    }
  };

  const handleApply = async () => {
    if (!result) return;
    setSaving(true);
    try {
      const shifts = result.shifts.map((s) => ({
        ...s,
        // Planned in local time; send absolute timestamps
        start_time: dayjs(s.start_time).toISOString(),
        end_time: dayjs(s.end_time).toISOString(),
      }));
      const response = await aiService.applyOptimization(shifts);
      message.success(`${response.created_count} shifts saved to the schedule.`);
      setSaveModalOpen(false);
      setResult(null);
    } catch {
      message.error('Could not save the schedule.');
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------- exports
  const rows = (result?.shifts ?? []).map((s) => ({
    Employee: s.employee_name,
    Department: s.department_name,
    Date: dayjs(s.start_time).format('YYYY-MM-DD'),
    Day: dayjs(s.start_time).format('dddd'),
    Shift: SHIFT_LOOKUP[s.shift_type]?.label ?? s.shift_type,
    Start: dayjs(s.start_time).format('HH:mm'),
    End: dayjs(s.end_time).format('HH:mm'),
    Hours: dayjs(s.end_time).diff(dayjs(s.start_time), 'hour', true).toFixed(1),
    'Preferred shift': s.preferred ? 'Yes' : 'No',
  }));
  const fileStamp = dayjs().format('YYYY-MM-DD_HH-mm');

  const exportToExcel = () => {
    if (!result) return;
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(rows), 'Schedule');
    const summary = [
      { Metric: 'Optimization score', Value: result.optimization_score },
      { Metric: 'Coverage (%)', Value: result.metrics?.coverage },
      { Metric: 'Preference match (%)', Value: result.metrics?.preference_match },
      { Metric: 'Fairness (%)', Value: result.metrics?.fairness },
      { Metric: 'Total shifts', Value: result.shifts.length },
      { Metric: 'Warnings', Value: result.conflicts.length },
    ];
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(summary), 'Summary');
    if (result.conflicts.length) {
      XLSX.utils.book_append_sheet(
        workbook,
        XLSX.utils.json_to_sheet(result.conflicts.map((c) => ({ Type: c.type, Message: c.message }))),
        'Warnings'
      );
    }
    const buffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    saveAs(new Blob([buffer], { type: 'application/octet-stream' }), `Schedule_${fileStamp}.xlsx`);
  };

  const exportToCSV = () => {
    if (!result) return;
    const csv = XLSX.utils.sheet_to_csv(XLSX.utils.json_to_sheet(rows));
    saveAs(new Blob([csv], { type: 'text/csv;charset=utf-8;' }), `Schedule_${fileStamp}.csv`);
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(
      rows.map((r) => `${r.Employee} | ${r.Department} | ${r.Date} | ${r.Start}–${r.End}`).join('\n')
    );
    message.success('Schedule copied to clipboard.');
  };

  const printSchedule = () => {
    if (!result) return;
    const html = `<html><head><title>Schedule ${dayjs().format('YYYY-MM-DD')}</title>
      <style>body{font-family:Arial,sans-serif;padding:24px}h1{color:#1e3a5f}table{width:100%;border-collapse:collapse;margin-top:16px}
      th,td{border:1px solid #ddd;padding:6px;text-align:left;font-size:12px}th{background:#1e3a5f;color:#fff}</style></head><body>
      <h1>Optimized Shift Schedule</h1>
      <p>Score ${result.optimization_score}/100 · ${result.shifts.length} shifts · ${result.conflicts.length} warnings</p>
      <table><thead><tr><th>Employee</th><th>Department</th><th>Date</th><th>Shift</th><th>Time</th></tr></thead><tbody>
      ${rows.map((r) => `<tr><td>${r.Employee}</td><td>${r.Department}</td><td>${r.Date}</td><td>${r.Shift}</td><td>${r.Start}–${r.End}</td></tr>`).join('')}
      </tbody></table></body></html>`;
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
      win.print();
    }
  };

  const exportMenu: MenuProps['items'] = [
    { key: 'excel', icon: <FileExcelOutlined style={{ color: '#16a34a' }} />, label: 'Excel (.xlsx)', onClick: exportToExcel },
    { key: 'csv', icon: <FileTextOutlined style={{ color: '#2563eb' }} />, label: 'CSV (.csv)', onClick: exportToCSV },
    { type: 'divider' },
    { key: 'print', icon: <PrinterOutlined />, label: 'Print', onClick: printSchedule },
    { key: 'copy', icon: <CopyOutlined />, label: 'Copy to clipboard', onClick: copyToClipboard },
  ];

  // ---------------------------------------------------------------- results
  const shiftCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    result?.shifts.forEach((s) => (counts[s.shift_type] = (counts[s.shift_type] ?? 0) + 1));
    return counts;
  }, [result]);

  const visibleShifts = useMemo(
    () => (result?.shifts ?? []).filter((s) => shiftFilter === 'all' || s.shift_type === shiftFilter),
    [result, shiftFilter]
  );

  const columns: ColumnsType<OptimizedShift> = [
    { title: 'Employee', dataIndex: 'employee_name', key: 'employee_name', sorter: (a, b) => (a.employee_name ?? '').localeCompare(b.employee_name ?? '') },
    { title: 'Department', dataIndex: 'department_name', key: 'department_name' },
    {
      title: 'Date',
      dataIndex: 'start_time',
      key: 'date',
      render: (v: string) => dayjs(v).format('ddd, MMM D'),
      sorter: (a, b) => dayjs(a.start_time).valueOf() - dayjs(b.start_time).valueOf(),
    },
    {
      title: 'Shift',
      dataIndex: 'shift_type',
      key: 'shift_type',
      render: (key: ShiftTypeKey) => <Tag color={SHIFT_LOOKUP[key]?.color}>{SHIFT_LOOKUP[key]?.label ?? key}</Tag>,
    },
    {
      title: 'Time',
      key: 'time',
      render: (_, r) => `${dayjs(r.start_time).format('HH:mm')} – ${dayjs(r.end_time).format('HH:mm')}`,
    },
    {
      title: 'Preference',
      dataIndex: 'preferred',
      key: 'preferred',
      render: (preferred: boolean) =>
        preferred ? <Tag icon={<HeartOutlined />} color="success">Preferred</Tag> : <Tag>Assigned</Tag>,
    },
  ];

  return (
    <DashboardLayout>
      <Spin spinning={dataLoading}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>AI Shift Optimization</Title>
            <Text type="secondary">Generate a schedule that respects labor rules, availability and employee preferences.</Text>
          </div>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh data</Button>
        </div>

        <Card variant="borderless" style={{ marginBottom: 24 }}>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={8}>
              <Card size="small" style={{ background: '#f0f9ff' }}>
                <Statistic title="Employees in scope" value={scopedEmployees.length} prefix={<TeamOutlined />} />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card size="small" style={{ background: '#f0fdf4' }}>
                <Statistic title="With shift preferences" value={withPreferences} prefix={<HeartOutlined />} suffix={`/ ${scopedEmployees.length}`} />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card size="small" style={{ background: '#fefce8' }}>
                <Statistic title="Departments" value={selectedDepartments.length || departments.length} prefix={<HomeOutlined />} suffix={selectedDepartments.length ? 'selected' : 'all'} />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>Planning period</Text>
              <RangePicker
                value={dateRange}
                onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])}
                style={{ width: '100%' }}
                disabledDate={(current) => current && current < dayjs().startOf('day')}
              />
            </Col>
            <Col xs={24} md={8}>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>Departments</Text>
              <Select
                mode="multiple"
                placeholder="All departments"
                style={{ width: '100%' }}
                value={selectedDepartments}
                onChange={setSelectedDepartments}
                allowClear
                options={departments.map((d) => ({ value: d.id, label: d.name }))}
              />
            </Col>
            <Col xs={12} md={4}>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>24/7 operation</Text>
              <Switch checked={settings.is_24_7} onChange={(v) => update('is_24_7', v)} />
            </Col>
            <Col xs={12} md={4}>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>Use preferences</Text>
              <Switch checked={settings.consider_preferences} onChange={(v) => update('consider_preferences', v)} />
            </Col>
          </Row>

          <Divider style={{ margin: '24px 0 16px' }} />
          <div
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <Space>
              <SettingOutlined />
              <Text strong>Constraints & weights</Text>
              {!showAdvanced && <Badge count="+" style={{ backgroundColor: '#1e3a5f' }} />}
            </Space>
            <Text type="secondary">{showAdvanced ? 'Hide' : 'Show'}</Text>
          </div>

          {showAdvanced && (
            <div style={{ marginTop: 20, padding: 20, background: '#f8fafc', borderRadius: 12 }}>
              <Row gutter={[24, 24]}>
                <Col xs={24} md={12}>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}><CalendarOutlined /> Operating days</Text>
                  <Checkbox.Group value={settings.operating_days} onChange={(v) => update('operating_days', v as string[])} disabled={settings.is_24_7}>
                    <Row>
                      {WEEK_DAYS.map((d) => (
                        <Col span={12} key={d.key}><Checkbox value={d.key}>{d.label}</Checkbox></Col>
                      ))}
                    </Row>
                  </Checkbox.Group>
                </Col>
                <Col xs={24} md={12}>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}><ClockCircleOutlined /> Shift types</Text>
                  <Checkbox.Group value={settings.shift_types} onChange={(v) => update('shift_types', v as ShiftTypeKey[])}>
                    <Row>
                      {SHIFT_TYPES.map((s) => (
                        <Col span={12} key={s.key}>
                          <Checkbox value={s.key}><Tag color={s.color}>{s.label}</Tag><Text type="secondary" style={{ fontSize: 12 }}>{s.time}</Text></Checkbox>
                        </Col>
                      ))}
                    </Row>
                  </Checkbox.Group>
                </Col>

                {([
                  ['min_employees_per_shift', 'Min people per shift', 0, 50, undefined],
                  ['max_employees_per_shift', 'Max people per shift', 1, 100, undefined],
                  ['max_hours_per_week', 'Max hours per week', 10, 80, 'h'],
                  ['max_consecutive_days', 'Max consecutive days', 1, 7, 'days'],
                  ['min_rest_hours', 'Min rest between shifts', 0, 24, 'h'],
                ] as const).map(([key, label, min, max, suffix]) => (
                  <Col xs={24} sm={12} md={8} key={key}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>{label}</Text>
                    <InputNumber
                      min={min}
                      max={max}
                      value={settings[key] as number}
                      onChange={(v) => update(key, (v ?? min) as never)}
                      style={{ width: '100%' }}
                      suffix={suffix}
                    />
                  </Col>
                ))}
                <Col xs={24} sm={12} md={8}>
                  <Text strong style={{ display: 'block', marginBottom: 8 }}>
                    Preference weight <Tooltip title="Higher values favour preferred shifts over perfectly even workload."><Text type="secondary">(?)</Text></Tooltip>
                  </Text>
                  <Slider
                    min={0}
                    max={100}
                    value={settings.preference_weight}
                    onChange={(v) => update('preference_weight', v)}
                    disabled={!settings.consider_preferences}
                    tooltip={{ formatter: (v) => `${v}%` }}
                  />
                </Col>
                <Col xs={24}>
                  <Space size="large" wrap>
                    <Space><Switch checked={settings.allow_overtime} onChange={(v) => update('allow_overtime', v)} /><Text>Allow overtime</Text></Space>
                    <Space><Switch checked={settings.balance_workload} onChange={(v) => update('balance_workload', v)} /><Text>Balance workload</Text></Space>
                  </Space>
                </Col>
              </Row>
            </div>
          )}

          <div style={{ marginTop: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <Button type="primary" size="large" icon={<ThunderboltOutlined />} onClick={handleOptimize} loading={running} disabled={!scopedEmployees.length}>
              Generate schedule ({scopedEmployees.length} employees)
            </Button>
            {result && (
              <Button size="large" icon={<FilterOutlined />} onClick={() => setResult(null)}>Reset</Button>
            )}
          </div>
        </Card>

        {running && (
          <Card variant="borderless" style={{ textAlign: 'center', padding: '48px 0' }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
              <Text strong>Optimizing schedule…</Text>
              <br />
              <Text type="secondary">Checking hour caps, rest periods and days off for {scopedEmployees.length} employees.</Text>
            </Paragraph>
          </Card>
        )}

        {result && !running && (
          <>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col xs={24} md={6}>
                <Card variant="borderless" style={{ height: '100%', textAlign: 'center' }}>
                  <Progress
                    type="dashboard"
                    percent={result.optimization_score}
                    strokeColor={scoreColor(result.optimization_score)}
                    format={(v) => <span style={{ fontSize: 28, fontWeight: 600 }}>{v}</span>}
                  />
                  <div><Text strong>Optimization score</Text></div>
                </Card>
              </Col>
              <Col xs={24} md={18}>
                <Card variant="borderless" style={{ height: '100%' }}>
                  <Row gutter={[24, 16]}>
                    {result.metrics && ([
                      ['Coverage', result.metrics.coverage, 'Share of required slots that were filled'],
                      ['Preference match', result.metrics.preference_match, 'Assignments that match the employee’s preferred shift'],
                      ['Fairness', result.metrics.fairness, 'How evenly hours are spread across the team'],
                    ] as const).map(([label, value, hint]) => (
                      <Col xs={24} sm={8} key={label}>
                        <Tooltip title={hint}><Text type="secondary">{label}</Text></Tooltip>
                        <Progress percent={value} strokeColor={scoreColor(value)} />
                      </Col>
                    ))}
                    <Col xs={12} sm={6}><Statistic title="Shifts" value={result.shifts.length} /></Col>
                    <Col xs={12} sm={6}><Statistic title="People scheduled" value={result.metrics?.employees_scheduled ?? 0} /></Col>
                    <Col xs={12} sm={6}><Statistic title="Planned hours" value={result.metrics?.total_hours ?? 0} suffix="h" /></Col>
                    <Col xs={12} sm={6}>
                      <Statistic
                        title="Warnings"
                        value={result.conflicts.length}
                        prefix={result.conflicts.length ? <WarningOutlined /> : <CheckCircleOutlined />}
                        styles={{ content: { color: result.conflicts.length ? '#d97706' : '#16a34a' } }}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>

            {result.conflicts.length > 0 && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 24 }}
                title={`${result.conflicts.length} item(s) need attention`}
                description={
                  <ul style={{ margin: 0, paddingLeft: 20, maxHeight: 160, overflow: 'auto' }}>
                    {result.conflicts.slice(0, 50).map((c, i) => (
                      <li key={i}><Tag color={c.type === 'overtime' ? 'orange' : 'red'}>{c.type.toUpperCase()}</Tag>{c.message}</li>
                    ))}
                  </ul>
                }
              />
            )}

            <Card
              variant="borderless"
              title={`Generated shifts (${visibleShifts.length})`}
              extra={
                <Space wrap>
                  <Select
                    value={shiftFilter}
                    onChange={setShiftFilter}
                    style={{ width: 170 }}
                    options={[
                      { value: 'all', label: `All shift types (${result.shifts.length})` },
                      ...SHIFT_TYPES.filter((s) => shiftCounts[s.key]).map((s) => ({ value: s.key, label: `${s.label} (${shiftCounts[s.key]})` })),
                    ]}
                  />
                  <Dropdown menu={{ items: exportMenu }} placement="bottomRight">
                    <Button icon={<DownloadOutlined />}>Export</Button>
                  </Dropdown>
                  <Button type="primary" icon={<SaveOutlined />} onClick={() => setSaveModalOpen(true)}>Save schedule</Button>
                </Space>
              }
            >
              <Table
                columns={columns}
                dataSource={visibleShifts}
                rowKey="id"
                size="middle"
                pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (total) => `${total} shifts` }}
                scroll={{ x: 760 }}
              />
            </Card>
          </>
        )}

        {!result && !running && (
          <Card variant="borderless" style={{ textAlign: 'center', padding: '40px 0' }}>
            <Result
              icon={<RobotOutlined style={{ color: '#1e3a5f' }} />}
              title="Ready to optimize"
              subTitle={
                scopedEmployees.length
                  ? `Pick a planning period and click “Generate schedule”. Nothing is saved until you review and confirm.`
                  : 'No employees yet. Add employees first.'
              }
              extra={
                <Space orientation="vertical">
                  <Text type="secondary"><CheckCircleOutlined style={{ color: '#16a34a' }} /> Weekly hour caps, rest periods and consecutive-day limits</Text>
                  <Text type="secondary"><CheckCircleOutlined style={{ color: '#16a34a' }} /> Preferred shifts and weekly days off</Text>
                  <Text type="secondary"><CheckCircleOutlined style={{ color: '#16a34a' }} /> Existing shifts in the period are taken into account</Text>
                </Space>
              }
            />
          </Card>
        )}

        <Modal
          title="Save schedule"
          open={saveModalOpen}
          onCancel={() => setSaveModalOpen(false)}
          onOk={handleApply}
          okText="Confirm and save"
          confirmLoading={saving}
        >
          <Paragraph>Add {result?.shifts.length} shifts to the schedule?</Paragraph>
          {result && result.conflicts.length > 0 && (
            <Alert type="warning" showIcon title={`This schedule has ${result.conflicts.length} warning(s).`} />
          )}
        </Modal>
      </Spin>
    </DashboardLayout>
  );
}
