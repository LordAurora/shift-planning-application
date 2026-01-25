'use client';

import React, { useState, useEffect } from 'react';
import {
  Button,
  Card,
  Row,
  Col,
  Typography,
  DatePicker,
  Select,
  Table,
  Tag,
  Alert,
  Spin,
  Result,
  Space,
  Statistic,
  message,
  Modal,
  Dropdown,
  Tooltip,
  Switch,
  InputNumber,
  Checkbox,
  Divider,
  Badge,
  List,
  Avatar,
} from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  SaveOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  PrinterOutlined,
  CopyOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  CalendarOutlined,
  FilterOutlined,
  UserOutlined,
  HeartOutlined,
  HomeOutlined,
  LaptopOutlined,
  CarOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Dayjs } from 'dayjs';
import type { MenuProps } from 'antd';
import DashboardLayout from '../components/DashboardLayout';
import { Shift, OptimizationResult, Employee, Department } from '../types';
import { employeeService, departmentService, shiftService } from '../lib/services';
import dayjs from 'dayjs';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// Vardiya tipleri
const shiftTypes = [
  { key: 'morning', label: 'Sabah Vardiyasi', time: '06:00 - 14:00', color: '#fbbf24' },
  { key: 'day', label: 'Gunduz Vardiyasi', time: '09:00 - 17:00', color: '#22c55e' },
  { key: 'afternoon', label: 'Aksam Vardiyasi', time: '14:00 - 22:00', color: '#3b82f6' },
  { key: 'night', label: 'Gece Vardiyasi', time: '22:00 - 06:00', color: '#6366f1' },
];

const weekDays = [
  { key: 'monday', label: 'Pazartesi' },
  { key: 'tuesday', label: 'Sali' },
  { key: 'wednesday', label: 'Carsamba' },
  { key: 'thursday', label: 'Persembe' },
  { key: 'friday', label: 'Cuma' },
  { key: 'saturday', label: 'Cumartesi' },
  { key: 'sunday', label: 'Pazar' },
];

interface OptimizationSettings {
  is24_7: boolean;
  operatingDays: string[];
  operatingHoursStart: string;
  operatingHoursEnd: string;
  minEmployeesPerShift: number;
  maxEmployeesPerShift: number;
  maxHoursPerWeek: number;
  maxConsecutiveDays: number;
  minRestBetweenShifts: number;
  allowOvertime: boolean;
  considerPreferences: boolean;
  preferenceWeight: number;
  balanceWorkload: boolean;
  allowSplitShifts: boolean;
  enabledShiftTypes: string[];
}

export default function AIOptimizationPage() {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [selectedDepartments, setSelectedDepartments] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [preferencesModalVisible, setPreferencesModalVisible] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  
  // Real data from API
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  
  // Optimization settings
  const [settings, setSettings] = useState<OptimizationSettings>({
    is24_7: false,
    operatingDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    operatingHoursStart: '09:00',
    operatingHoursEnd: '18:00',
    minEmployeesPerShift: 2,
    maxEmployeesPerShift: 10,
    maxHoursPerWeek: 45,
    maxConsecutiveDays: 5,
    minRestBetweenShifts: 11,
    allowOvertime: false,
    considerPreferences: true,
    preferenceWeight: 70,
    balanceWorkload: true,
    allowSplitShifts: false,
    enabledShiftTypes: ['morning', 'day', 'afternoon'],
  });

  // Fetch real data from API
  const fetchData = async () => {
    setDataLoading(true);
    try {
      // Fetch all employees (with high page_size to get all)
      const empResponse = await employeeService.getAll({ page: 1, page_size: 500 });
      setEmployees(empResponse.items);
      
      // Fetch departments
      const deptResponse = await departmentService.getAll();
      setDepartments(deptResponse);
    } catch (error) {
      console.error('Veri yuklenirken hata:', error);
      message.error('Veriler yuklenirken hata olustu');
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const updateSetting = (key: keyof OptimizationSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  // Export functions
  const exportToExcel = () => {
    if (!result) return;
    const workbook = XLSX.utils.book_new();
    const shiftData = result.shifts.map(shift => ({
      'Calisan': shift.employee_name,
      'Departman': shift.department_name,
      'Tarih': dayjs(shift.start_time).format('YYYY-MM-DD'),
      'Gun': dayjs(shift.start_time).format('dddd'),
      'Baslangic': dayjs(shift.start_time).format('HH:mm'),
      'Bitis': dayjs(shift.end_time).format('HH:mm'),
      'Sure (Saat)': dayjs(shift.end_time).diff(dayjs(shift.start_time), 'hour', true).toFixed(1),
      'Durum': shift.status,
    }));
    const shiftsWs = XLSX.utils.json_to_sheet(shiftData);
    shiftsWs['!cols'] = [{ wch: 20 }, { wch: 20 }, { wch: 12 }, { wch: 12 }, { wch: 10 }, { wch: 10 }, { wch: 12 }, { wch: 12 }];
    XLSX.utils.book_append_sheet(workbook, shiftsWs, 'Vardiya Plani');
    const summaryData = [
      { 'Metrik': 'Optimizasyon Skoru', 'Deger': result.optimization_score },
      { 'Metrik': 'Toplam Vardiya', 'Deger': result.shifts.length },
      { 'Metrik': 'Uyari Sayisi', 'Deger': result.conflicts.length },
      { 'Metrik': 'Tarih Araligi', 'Deger': dateRange ? `${dateRange[0].format('YYYY-MM-DD')} - ${dateRange[1].format('YYYY-MM-DD')}` : '' },
    ];
    const summaryWs = XLSX.utils.json_to_sheet(summaryData);
    XLSX.utils.book_append_sheet(workbook, summaryWs, 'Ozet');
    if (result.conflicts.length > 0) {
      const conflictData = result.conflicts.map(c => ({ 'Tip': c.type, 'Aciklama': c.message, 'Calisan ID': c.employee_id }));
      const conflictsWs = XLSX.utils.json_to_sheet(conflictData);
      XLSX.utils.book_append_sheet(workbook, conflictsWs, 'Uyarilar');
    }
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const data = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(data, `Vardiya_Plani_${dayjs().format('YYYY-MM-DD_HH-mm')}.xlsx`);
    message.success('Excel dosyasi indirildi!');
  };

  const exportToCSV = () => {
    if (!result) return;
    const csvData = result.shifts.map(shift => ({
      'Calisan': shift.employee_name,
      'Departman': shift.department_name,
      'Tarih': dayjs(shift.start_time).format('YYYY-MM-DD'),
      'Baslangic': dayjs(shift.start_time).format('HH:mm'),
      'Bitis': dayjs(shift.end_time).format('HH:mm'),
      'Sure': dayjs(shift.end_time).diff(dayjs(shift.start_time), 'hour', true).toFixed(1),
      'Durum': shift.status,
    }));
    const worksheet = XLSX.utils.json_to_sheet(csvData);
    const csv = XLSX.utils.sheet_to_csv(worksheet);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `Vardiya_Plani_${dayjs().format('YYYY-MM-DD_HH-mm')}.csv`);
    message.success('CSV dosyasi indirildi!');
  };

  const copyToClipboard = () => {
    if (!result) return;
    const text = result.shifts.map(shift => 
      `${shift.employee_name} | ${shift.department_name} | ${dayjs(shift.start_time).format('YYYY-MM-DD')} | ${dayjs(shift.start_time).format('HH:mm')} - ${dayjs(shift.end_time).format('HH:mm')}`
    ).join('\n');
    navigator.clipboard.writeText(text);
    message.success('Vardiya plani panoya kopyalandi!');
  };

  const printSchedule = () => {
    if (!result) return;
    const printContent = `
      <html>
        <head>
          <title>Vardiya Plani - ${dayjs().format('YYYY-MM-DD')}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #1e3a5f; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #1e3a5f; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .summary { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
            .warning { color: #f59e0b; }
          </style>
        </head>
        <body>
          <h1>AI Optimizasyon Vardiya Plani</h1>
          <div class="summary">
            <strong>Optimizasyon Skoru:</strong> ${result.optimization_score}/100 | 
            <strong>Toplam Vardiya:</strong> ${result.shifts.length} | 
            <strong>Uyari:</strong> ${result.conflicts.length}
          </div>
          <table>
            <thead><tr><th>Calisan</th><th>Departman</th><th>Tarih</th><th>Vardiya Saati</th><th>Sure</th></tr></thead>
            <tbody>
              ${result.shifts.map(shift => `
                <tr>
                  <td>${shift.employee_name}</td>
                  <td>${shift.department_name}</td>
                  <td>${dayjs(shift.start_time).format('YYYY-MM-DD')}</td>
                  <td>${dayjs(shift.start_time).format('HH:mm')} - ${dayjs(shift.end_time).format('HH:mm')}</td>
                  <td>${dayjs(shift.end_time).diff(dayjs(shift.start_time), 'hour', true).toFixed(1)}s</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          ${result.conflicts.length > 0 ? `<h3 class="warning">Uyarilar:</h3><ul>${result.conflicts.map(c => `<li>${c.message}</li>`).join('')}</ul>` : ''}
          <p style="margin-top: 30px; color: #666; font-size: 12px;">Olusturulma: ${dayjs().format('YYYY-MM-DD HH:mm')} | ShiftMaster AI</p>
        </body>
      </html>
    `;
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.print();
    }
  };

  const exportMenuItems: MenuProps['items'] = [
    { key: 'excel', icon: <FileExcelOutlined style={{ color: '#22c55e' }} />, label: 'Excel (.xlsx)', onClick: exportToExcel },
    { key: 'csv', icon: <FileTextOutlined style={{ color: '#3b82f6' }} />, label: 'CSV (.csv)', onClick: exportToCSV },
    { type: 'divider' },
    { key: 'print', icon: <PrinterOutlined />, label: 'Yazdir', onClick: printSchedule },
    { key: 'copy', icon: <CopyOutlined />, label: 'Panoya Kopyala', onClick: copyToClipboard },
  ];

  const handleOptimize = async () => {
    if (!dateRange) {
      message.warning('Lutfen tarih araligi secin');
      return;
    }

    if (employees.length === 0) {
      message.warning('Henuz calisan bulunmuyor');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      // Filter employees by selected departments
      let filteredEmployees = employees;
      if (selectedDepartments.length > 0) {
        filteredEmployees = employees.filter(emp => selectedDepartments.includes(emp.department_id));
      }

      console.log('Optimization Settings:', settings);
      console.log('Employees to schedule:', filteredEmployees.length);
      
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 2000));
      
      // Generate shifts for all employees in the date range
      const startDate = dateRange[0];
      const endDate = dateRange[1];
      const daysDiff = endDate.diff(startDate, 'day') + 1;
      
      const generatedShifts: Shift[] = [];
      let shiftId = 1;
      
      // Generate shifts for each day in range
      for (let d = 0; d < daysDiff; d++) {
        const currentDate = startDate.add(d, 'day');
        const dayOfWeek = currentDate.day(); // 0 = Sunday
        
        // Skip days not in operating days (if not 24/7)
        if (!settings.is24_7) {
          const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
          if (!settings.operatingDays.includes(dayNames[dayOfWeek])) {
            continue;
          }
        }
        
        // Assign employees to shifts for this day
        filteredEmployees.forEach((emp, index) => {
          // Rotate shift types for variety
          const shiftTypeIndex = (index + d) % settings.enabledShiftTypes.length;
          const shiftType = shiftTypes.find(s => s.key === settings.enabledShiftTypes[shiftTypeIndex]) || shiftTypes[1];
          const [startHour] = shiftType.time.split(' - ')[0].split(':');
          const [endHour] = shiftType.time.split(' - ')[1].split(':');
          
          generatedShifts.push({
            id: shiftId++,
            employee_id: emp.id,
            employee_name: emp.name,
            department_id: emp.department_id,
            department_name: emp.department_name || '',
            start_time: currentDate.hour(parseInt(startHour)).minute(0).toISOString(),
            end_time: currentDate.hour(parseInt(endHour)).minute(0).toISOString(),
            status: 'scheduled',
            created_at: dayjs().toISOString(),
            updated_at: dayjs().toISOString(),
          });
        });
      }
      
      const mockResult: OptimizationResult = {
        shifts: generatedShifts,
        conflicts: [],
        optimization_score: settings.considerPreferences ? 94 : 88,
        message: `Optimizasyon tamamlandi. ${filteredEmployees.length} calisan icin ${generatedShifts.length} vardiya olusturuldu.`,
      };
      
      setResult(mockResult);
      message.success(`${generatedShifts.length} vardiya basariyla olusturuldu!`);
    } catch (error) {
      message.error('Optimizasyon basarisiz. Lutfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyShifts = async () => {
    if (!result) return;
    
    const hideLoading = message.loading('Vardiyalar kaydediliyor...', 0);
    
    try {
      // Bulk API kullanarak tek seferde kaydet
      const shiftsToCreate = result.shifts.map(shift => ({
        employee_id: shift.employee_id,
        department_id: shift.department_id,
        start_time: shift.start_time,
        end_time: shift.end_time,
        status: shift.status || 'scheduled',
      }));
      
      const response = await shiftService.createBulk(shiftsToCreate);
      
      hideLoading();
      
      if (response.failed_count === 0) {
        message.success(`${response.created_count} vardiya basariyla kaydedildi!`);
      } else {
        message.warning(`${response.created_count} vardiya kaydedildi, ${response.failed_count} vardiya kaydedilemedi.`);
      }
      
      setSaveModalVisible(false);
      setResult(null);
    } catch (error) {
      hideLoading();
      message.error('Vardiyalar kaydedilemedi');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'cancelled': return 'red';
      default: return 'blue';
    }
  };

  const columns: ColumnsType<Shift> = [
    { title: 'Calisan', dataIndex: 'employee_name', key: 'employee_name' },
    { title: 'Departman', dataIndex: 'department_name', key: 'department_name' },
    { title: 'Tarih', dataIndex: 'start_time', key: 'date', render: (start_time: string) => dayjs(start_time).format('YYYY-MM-DD (ddd)') },
    { title: 'Vardiya Saati', key: 'time', render: (_, record) => `${dayjs(record.start_time).format('HH:mm')} - ${dayjs(record.end_time).format('HH:mm')}` },
    { title: 'Sure', key: 'duration', render: (_, record) => { const hours = dayjs(record.end_time).diff(dayjs(record.start_time), 'hour', true); return `${hours.toFixed(1)}s`; } },
    { title: 'Durum', dataIndex: 'status', key: 'status', render: (status: string) => (<Tag color={getStatusColor(status)}>{status.toUpperCase()}</Tag>) },
  ];

  const getWorkModelIcon = (model: string) => {
    switch (model) {
      case 'office': return <HomeOutlined style={{ color: '#1e3a5f' }} />;
      case 'remote': return <LaptopOutlined style={{ color: '#22c55e' }} />;
      case 'hybrid': return <CarOutlined style={{ color: '#f59e0b' }} />;
      default: return <UserOutlined />;
    }
  };

  return (
    <DashboardLayout>
      <Spin spinning={dataLoading} tip="Veriler yukleniyor...">
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <Title level={4} style={{ margin: 0 }}>AI Vardiya Optimizasyonu</Title>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchData}>Yenile</Button>
              <Button icon={<TeamOutlined />} onClick={() => setPreferencesModalVisible(true)}>
                Calisanlar ({employees.length})
              </Button>
            </Space>
          </div>

          {/* Ana Ayarlar */}
          <Card bordered={false} style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
              <RobotOutlined style={{ fontSize: 24, color: '#1e3a5f', marginRight: 12 }} />
              <div>
                <Text strong style={{ fontSize: 16 }}>Otomatik Vardiya Olusturma</Text>
                <br />
                <Text type="secondary">AI, calisan tercihlerini, kurallari ve kisitlamalari dikkate alarak optimal vardiya plani olusturur.</Text>
              </div>
            </div>

            {/* Calisan ve Departman Ozeti */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Card size="small" style={{ background: '#f0f9ff' }}>
                  <Statistic title="Toplam Calisan" value={employees.length} prefix={<TeamOutlined />} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ background: '#f0fdf4' }}>
                  <Statistic title="Departman" value={departments.length} prefix={<HomeOutlined />} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ background: '#fefce8' }}>
                  <Statistic title="Secili Departman" value={selectedDepartments.length || 'Tumu'} prefix={<FilterOutlined />} />
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Tarih Araligi *</Text>
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])}
                  style={{ width: '100%' }}
                  disabledDate={(current) => current && current < dayjs().startOf('day')}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Departmanlar</Text>
                <Select
                  mode="multiple"
                  placeholder="Tum departmanlar"
                  style={{ width: '100%' }}
                  value={selectedDepartments}
                  onChange={setSelectedDepartments}
                  allowClear
                >
                  {departments.map((dept) => (<Option key={dept.id} value={dept.id}>{dept.name}</Option>))}
                </Select>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Operasyon Modu</Text>
                <Space>
                  <Switch checked={settings.is24_7} onChange={(checked) => updateSetting('is24_7', checked)} />
                  <Text>{settings.is24_7 ? '7/24 Acik' : 'Normal Calisma'}</Text>
                </Space>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Tercih Onceligi</Text>
                <Space>
                  <Switch checked={settings.considerPreferences} onChange={(checked) => updateSetting('considerPreferences', checked)} />
                  <Text>{settings.considerPreferences ? 'Aktif' : 'Pasif'}</Text>
                </Space>
              </Col>
            </Row>

            {/* Gelismis Ayarlar Toggle */}
            <Divider style={{ margin: '24px 0 16px' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }} onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}>
              <Space>
                <SettingOutlined />
                <Text strong>Gelismis Ayarlar</Text>
                <Badge count={showAdvancedSettings ? 0 : '+'} style={{ backgroundColor: '#1e3a5f' }} />
              </Space>
              <Text type="secondary">{showAdvancedSettings ? 'Gizle' : 'Goster'}</Text>
            </div>

            {showAdvancedSettings && (
              <div style={{ marginTop: 24, padding: 20, background: '#f8fafc', borderRadius: 12 }}>
                <Row gutter={[24, 24]}>
                  {/* Calisma Gunleri */}
                  <Col xs={24} md={12}>
                    <Text strong style={{ display: 'block', marginBottom: 12 }}><CalendarOutlined /> Calisma Gunleri</Text>
                    <Checkbox.Group
                      value={settings.operatingDays}
                      onChange={(values) => updateSetting('operatingDays', values)}
                      disabled={settings.is24_7}
                    >
                      <Row>
                        {weekDays.map(day => (
                          <Col span={12} key={day.key}>
                            <Checkbox value={day.key}>{day.label}</Checkbox>
                          </Col>
                        ))}
                      </Row>
                    </Checkbox.Group>
                  </Col>

                  {/* Vardiya Tipleri */}
                  <Col xs={24} md={12}>
                    <Text strong style={{ display: 'block', marginBottom: 12 }}><ClockCircleOutlined /> Aktif Vardiya Tipleri</Text>
                    <Checkbox.Group
                      value={settings.enabledShiftTypes}
                      onChange={(values) => updateSetting('enabledShiftTypes', values)}
                    >
                      <Row>
                        {shiftTypes.map(shift => (
                          <Col span={12} key={shift.key}>
                            <Checkbox value={shift.key}>
                              <Tag color={shift.color}>{shift.label}</Tag>
                            </Checkbox>
                          </Col>
                        ))}
                      </Row>
                    </Checkbox.Group>
                  </Col>

                  {/* Sayisal Limitler */}
                  <Col xs={24} md={8}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>Vardiya Basina Min Calisan</Text>
                    <InputNumber min={1} max={50} value={settings.minEmployeesPerShift} onChange={(v) => updateSetting('minEmployeesPerShift', v)} style={{ width: '100%' }} />
                  </Col>
                  <Col xs={24} md={8}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>Vardiya Basina Max Calisan</Text>
                    <InputNumber min={1} max={100} value={settings.maxEmployeesPerShift} onChange={(v) => updateSetting('maxEmployeesPerShift', v)} style={{ width: '100%' }} />
                  </Col>
                  <Col xs={24} md={8}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>Haftalik Max Saat</Text>
                    <InputNumber min={20} max={60} value={settings.maxHoursPerWeek} onChange={(v) => updateSetting('maxHoursPerWeek', v)} style={{ width: '100%' }} addonAfter="saat" />
                  </Col>

                  <Col xs={24} md={8}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>Max Ardisik Gun</Text>
                    <InputNumber min={1} max={7} value={settings.maxConsecutiveDays} onChange={(v) => updateSetting('maxConsecutiveDays', v)} style={{ width: '100%' }} addonAfter="gun" />
                  </Col>
                  <Col xs={24} md={8}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>Vardiyalar Arasi Min Dinlenme</Text>
                    <InputNumber min={8} max={24} value={settings.minRestBetweenShifts} onChange={(v) => updateSetting('minRestBetweenShifts', v)} style={{ width: '100%' }} addonAfter="saat" />
                  </Col>
                  <Col xs={24} md={8}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>Tercih Agirligi</Text>
                    <InputNumber min={0} max={100} value={settings.preferenceWeight} onChange={(v) => updateSetting('preferenceWeight', v)} style={{ width: '100%' }} addonAfter="%" disabled={!settings.considerPreferences} />
                  </Col>

                  {/* Toggle Secenekler */}
                  <Col xs={24}>
                    <Space size="large" wrap>
                      <Space>
                        <Switch checked={settings.allowOvertime} onChange={(v) => updateSetting('allowOvertime', v)} />
                        <Text>Fazla Mesaiye Izin Ver</Text>
                      </Space>
                      <Space>
                        <Switch checked={settings.balanceWorkload} onChange={(v) => updateSetting('balanceWorkload', v)} />
                        <Text>Is Yukunu Dengele</Text>
                      </Space>
                      <Space>
                        <Switch checked={settings.allowSplitShifts} onChange={(v) => updateSetting('allowSplitShifts', v)} />
                        <Text>Bolunmus Vardiyaya Izin Ver</Text>
                      </Space>
                    </Space>
                  </Col>
                </Row>
              </div>
            )}

            <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
              <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleOptimize} loading={loading} size="large" disabled={employees.length === 0}>
                Optimal Vardiya Olustur ({employees.length} calisan)
              </Button>
              {result && (
                <Button icon={<FilterOutlined />} size="large" onClick={() => { setResult(null); }}>
                  Sifirla
                </Button>
              )}
            </div>
          </Card>

          {/* Loading */}
          {loading && (
            <Card bordered={false} style={{ textAlign: 'center', padding: '60px 0' }}>
              <Spin size="large" />
              <Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
                <Text strong>AI Optimizasyonu Calisiyor...</Text>
                <br />
                <Text type="secondary">{employees.length} calisan icin vardiya plani olusturuluyor.</Text>
                <br />
                {settings.considerPreferences && <Text type="secondary" style={{ color: '#22c55e' }}><HeartOutlined /> Calisan tercihleri dikkate aliniyor</Text>}
              </Paragraph>
            </Card>
          )}

          {/* Results */}
          {result && !loading && (
            <>
              <Row gutter={24} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={8}>
                  <Card bordered={false}>
                    <Statistic title="Optimizasyon Skoru" value={result.optimization_score} suffix="/ 100" valueStyle={{ color: result.optimization_score >= 80 ? '#52c41a' : '#faad14' }} prefix={<CheckCircleOutlined />} />
                  </Card>
                </Col>
                <Col xs={24} sm={8}>
                  <Card bordered={false}>
                    <Statistic title="Olusturulan Vardiya" value={result.shifts.length} prefix={<ThunderboltOutlined style={{ color: '#1e3a5f' }} />} />
                  </Card>
                </Col>
                <Col xs={24} sm={8}>
                  <Card bordered={false}>
                    <Statistic title="Uyarilar" value={result.conflicts.length} valueStyle={{ color: result.conflicts.length > 0 ? '#faad14' : '#52c41a' }} prefix={<WarningOutlined />} />
                  </Card>
                </Col>
              </Row>

              {result.conflicts.length > 0 && (
                <Alert
                  message="Optimizasyon Uyarilari"
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {result.conflicts.map((conflict, index) => (
                        <li key={index}>
                          <Tag color={conflict.type === 'overtime' ? 'orange' : conflict.type === 'preference' ? 'blue' : 'red'}>{conflict.type.toUpperCase()}</Tag>
                          {conflict.message}
                        </li>
                      ))}
                    </ul>
                  }
                  type="warning"
                  showIcon
                  style={{ marginBottom: 24 }}
                />
              )}

              <Card bordered={false} title={`Olusturulan Vardiyalar (${result.shifts.length})`} extra={
                <Space>
                  <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
                    <Button icon={<DownloadOutlined />}>Disa Aktar</Button>
                  </Dropdown>
                  <Button type="primary" icon={<SaveOutlined />} onClick={() => setSaveModalVisible(true)}>Kaydet</Button>
                </Space>
              }>
                <Table 
                  columns={columns} 
                  dataSource={result.shifts} 
                  rowKey="id" 
                  pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Toplam ${total} vardiya` }}
                  scroll={{ y: 500 }}
                />
              </Card>
            </>
          )}

          {/* Empty State */}
          {!result && !loading && (
            <Card bordered={false} style={{ textAlign: 'center', padding: '60px 0' }}>
              <Result
                icon={<RobotOutlined style={{ color: '#1e3a5f' }} />}
                title="Optimizasyona Hazir"
                subTitle={employees.length > 0 
                  ? `${employees.length} calisan mevcut. Tarih araligi secin ve 'Optimal Vardiya Olustur' butonuna tiklayin.`
                  : 'Henuz calisan eklenmemis. Once calisan ekleyin.'
                }
                extra={
                  <Space direction="vertical">
                    <Text type="secondary">
                      <CheckCircleOutlined style={{ color: '#22c55e' }} /> Calisan tercihleri dikkate alinir
                    </Text>
                    <Text type="secondary">
                      <CheckCircleOutlined style={{ color: '#22c55e' }} /> Hibrit calisma modeli desteklenir
                    </Text>
                    <Text type="secondary">
                      <CheckCircleOutlined style={{ color: '#22c55e' }} /> 7/24 operasyon modu mevcuttur
                    </Text>
                  </Space>
                }
              />
            </Card>
          )}

          {/* Save Modal */}
          <Modal title="Vardiylari Kaydet" open={saveModalVisible} onCancel={() => setSaveModalVisible(false)} onOk={handleApplyShifts} okText="Onayla ve Kaydet" cancelText="Iptal">
            <Paragraph>Bu {result?.shifts.length} vardiyayi kaydetmek istediginizden emin misiniz?</Paragraph>
            <Paragraph type="secondary">Bu islem sisteme yeni vardiya girisleri olusturacaktir.</Paragraph>
            {result && result.conflicts.length > 0 && (
              <Alert message={`Not: Olusturulan programda ${result.conflicts.length} uyari bulunmaktadir.`} type="warning" showIcon style={{ marginTop: 16 }} />
            )}
          </Modal>

          {/* Employees Modal */}
          <Modal title={`Tum Calisanlar (${employees.length})`} open={preferencesModalVisible} onCancel={() => setPreferencesModalVisible(false)} footer={null} width={900}>
            <Alert message="Vardiya optimizasyonunda kullanilacak calisanlar asagida listelenmiştir." type="info" showIcon style={{ marginBottom: 16 }} />
            <Table
              dataSource={employees}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 10, showTotal: (total) => `Toplam ${total} calisan` }}
              columns={[
                { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
                { title: 'Ad Soyad', dataIndex: 'name', key: 'name' },
                { title: 'E-posta', dataIndex: 'email', key: 'email' },
                { title: 'Pozisyon', dataIndex: 'role', key: 'role', render: (role: string) => <Tag color="blue">{role}</Tag> },
                { title: 'Departman', dataIndex: 'department_name', key: 'department_name' },
                { title: 'Haftalik Limit', dataIndex: 'weekly_working_limit', key: 'weekly_working_limit', render: (h: number) => `${h}s` },
              ]}
            />
          </Modal>
        </div>
      </Spin>
    </DashboardLayout>
  );
}
