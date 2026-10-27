'use client';

import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd';
import {
  BugOutlined,
  CloudServerOutlined,
  CodeOutlined,
  FireOutlined,
  ReloadOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  SecurityScanOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import dayjs from 'dayjs';
import { securityScanService } from '../lib/services';
import type { SecurityDashboardStats, SecurityScanResult, Vulnerability, VulnerabilitySeverity } from '../types';

const { Title, Text } = Typography;

const severityColors: Record<VulnerabilitySeverity, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
};
const severityOrder: VulnerabilitySeverity[] = ['critical', 'high', 'medium', 'low', 'info'];

const categoryLabel = (key: string) =>
  key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export default function SecurityDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<SecurityDashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setStats(await securityScanService.getDashboardStats());
    } catch {
      setError('Failed to load security dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <Alert
        title="Error"
        description={error}
        type="error"
        showIcon
        action={<Button onClick={load} size="small">Retry</Button>}
      />
    );
  }

  const totalSeverity = severityOrder.reduce((sum, s) => sum + (stats.severity_distribution[s] ?? 0), 0);
  const categories = Object.entries(stats.category_distribution).sort((a, b) => b[1] - a[1]);
  const maxCategory = categories[0]?.[1] ?? 0;
  const rules = stats.rule_engine;

  const scanColumns = [
    { title: 'File', dataIndex: 'filename', key: 'filename', render: (v: string) => <Text code>{v}</Text> },
    {
      title: 'Findings',
      key: 'summary',
      render: (_: unknown, r: SecurityScanResult) => (
        <Space size={4} wrap>
          {severityOrder.filter((s) => r.summary[s]).map((s) => (
            <Tag key={s} color={severityColors[s]}>{r.summary[s]} {s}</Tag>
          ))}
          {r.summary.total === 0 && <Tag color="success">Clean</Tag>}
        </Space>
      ),
    },
    { title: 'Mode', dataIndex: 'detection_mode', key: 'mode', render: (v: string) => v.replace('_', ' ') },
    { title: 'Duration', dataIndex: 'duration_ms', key: 'duration', render: (v: number) => `${v.toFixed(1)} ms` },
    { title: 'When', dataIndex: 'started_at', key: 'when', render: (v: string) => dayjs(v).format('MMM D, HH:mm') },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <SecurityScanOutlined style={{ marginRight: 12 }} />
            Security AI Dashboard
          </Title>
          <Text type="secondary">Results from scans run with the hybrid rule + ML detection engine</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
          <Button type="primary" icon={<SecurityScanOutlined />} onClick={() => router.push('/security/scan')}>New scan</Button>
        </Space>
      </div>

      {!stats.ml_model_loaded && (
        <Alert
          type="info"
          showIcon
          icon={<RobotOutlined />}
          style={{ marginBottom: 24 }}
          title="Running in rule-based mode"
          description="No trained ML model is loaded, so scans use the deterministic rule engine and model metrics are not reported. Train and deploy a model to enable hybrid detection."
        />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="Scans run" value={stats.total_scans} prefix={<SecurityScanOutlined style={{ color: '#3b82f6' }} />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Open findings"
              value={stats.open_vulnerabilities}
              prefix={<BugOutlined style={{ color: '#f97316' }} />}
              suffix={<Text type="secondary" style={{ fontSize: 14 }}>/ {stats.total_vulnerabilities}</Text>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Critical findings"
              value={stats.severity_distribution.critical ?? 0}
              prefix={<FireOutlined style={{ color: '#ef4444' }} />}
              styles={{ content: { color: stats.severity_distribution.critical ? '#ef4444' : undefined } }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Detection rules"
              value={rules?.enabled_rules ?? 0}
              prefix={<SafetyCertificateOutlined style={{ color: '#22c55e' }} />}
              suffix={<Text type="secondary" style={{ fontSize: 14 }}>{rules?.critical_rules ?? 0} critical</Text>}
            />
          </Card>
        </Col>
      </Row>

      {stats.total_scans === 0 ? (
        <Card style={{ marginBottom: 24 }}>
          <Empty description="No scans yet. Run your first scan to populate the dashboard.">
            <Button type="primary" onClick={() => router.push('/security/scan')}>Run a scan</Button>
          </Empty>
        </Card>
      ) : (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title={<Space><BugOutlined />Severity distribution</Space>} style={{ height: '100%' }}>
                {severityOrder.map((severity) => {
                  const count = stats.severity_distribution[severity] ?? 0;
                  return (
                    <div key={severity} style={{ marginBottom: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Tag color={severityColors[severity]} style={{ textTransform: 'uppercase' }}>{severity}</Tag>
                        <Text strong>{count}</Text>
                      </div>
                      <Progress percent={totalSeverity ? (count / totalSeverity) * 100 : 0} showInfo={false} strokeColor={severityColors[severity]} size="small" />
                    </div>
                  );
                })}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title={<Space><CodeOutlined />Findings by category</Space>} style={{ height: '100%' }}>
                {categories.map(([category, count]) => (
                  <div key={category} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text>{categoryLabel(category)}</Text>
                      <Text strong>{count}</Text>
                    </div>
                    <Progress percent={maxCategory ? (count / maxCategory) * 100 : 0} showInfo={false} strokeColor="#1e3a5f" size="small" />
                  </div>
                ))}
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} xl={14}>
              <Card title="Recent scans">
                <Table rowKey="scan_id" dataSource={stats.recent_scans} columns={scanColumns} pagination={false} size="small" scroll={{ x: 560 }} />
              </Card>
            </Col>
            <Col xs={24} xl={10}>
              <Card title="Top findings">
                {stats.top_vulnerabilities.map((v: Vulnerability) => (
                  <div key={v.id} style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <Space wrap>
                      <Tag color={severityColors[v.severity]}>{v.severity.toUpperCase()}</Tag>
                      <Text strong>{v.title}</Text>
                    </Space>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {v.file_path}{v.line_number ? `:${v.line_number}` : ''} · {v.cwe_id}
                      </Text>
                    </div>
                  </div>
                ))}
              </Card>
            </Col>
          </Row>
        </>
      )}

      <Row gutter={[16, 16]}>
        {[
          { href: '/security/scan', icon: <SecurityScanOutlined style={{ fontSize: 32, color: '#3b82f6' }} />, title: 'Run security scan', text: 'Analyze code with the detection engine' },
          { href: '/security/rules', icon: <CodeOutlined style={{ fontSize: 32, color: '#22c55e' }} />, title: 'Detection rules', text: 'Browse the active rule set' },
          { href: '/security/training', icon: <RobotOutlined style={{ fontSize: 32, color: '#8b5cf6' }} />, title: 'ML training', text: 'Training pipeline (preview)' },
          { href: '/security/migration', icon: <CloudServerOutlined style={{ fontSize: 32, color: '#f97316' }} />, title: 'MindSpore migration', text: 'Migration plan (preview)' },
        ].map((item) => (
          <Col xs={24} sm={12} lg={6} key={item.href}>
            <Card hoverable onClick={() => router.push(item.href)} style={{ textAlign: 'center', cursor: 'pointer' }}>
              {item.icon}
              <Title level={5} style={{ marginTop: 8 }}>{item.title}</Title>
              <Text type="secondary">{item.text}</Text>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
