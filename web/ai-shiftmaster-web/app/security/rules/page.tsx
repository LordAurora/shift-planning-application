'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Badge, Button, Card, Col, Input, Row, Select, Space, Statistic, Table, Tag, Typography, message } from 'antd';
import { CodeOutlined, ReloadOutlined, SafetyCertificateOutlined, SearchOutlined, FireOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { securityScanService } from '../../lib/services';
import type { EngineRule, VulnerabilitySeverity } from '../../types';

const { Title, Text, Paragraph } = Typography;

const severityColors: Record<VulnerabilitySeverity, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6',
};
const severityRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

export default function SecurityRulesPage() {
  const [rules, setRules] = useState<EngineRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState<string | undefined>();

  const load = async () => {
    setLoading(true);
    try {
      setRules(await securityScanService.getEngineRules());
    } catch {
      message.error('Failed to load detection rules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(
    () =>
      rules
        .filter((r) => !severity || r.severity === severity)
        .filter((r) => !search || `${r.id} ${r.name} ${r.description} ${r.cwe_id}`.toLowerCase().includes(search.toLowerCase()))
        .sort((a, b) => severityRank[a.severity] - severityRank[b.severity]),
    [rules, search, severity]
  );

  const columns: ColumnsType<EngineRule> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 100, render: (id: string) => <Text code>{id}</Text> },
    {
      title: 'Rule',
      key: 'rule',
      render: (_, r) => (
        <div>
          <Text strong>{r.name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{r.description}</Text>
        </div>
      ),
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 110,
      render: (s: VulnerabilitySeverity) => <Tag color={severityColors[s]} style={{ textTransform: 'uppercase' }}>{s}</Tag>,
    },
    { title: 'OWASP', dataIndex: 'category', key: 'category', width: 260, render: (c: string) => <Text style={{ fontSize: 12 }}>{c}</Text> },
    { title: 'CWE', dataIndex: 'cwe_id', key: 'cwe', width: 100 },
    { title: 'Patterns', dataIndex: 'patterns', key: 'patterns', width: 90, align: 'center' },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean) => <Badge status={enabled ? 'success' : 'default'} text={enabled ? 'Active' : 'Disabled'} />,
    },
  ];

  const critical = rules.filter((r) => r.severity === 'critical').length;
  const owasp = new Set(rules.map((r) => r.category)).size;

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <CodeOutlined style={{ marginRight: 12 }} />
            Detection Rules
          </Title>
          <Text type="secondary">Deterministic rules loaded in the hybrid detection engine</Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}><Card><Statistic title="Active rules" value={rules.filter((r) => r.enabled).length} prefix={<SafetyCertificateOutlined style={{ color: '#22c55e' }} />} /></Card></Col>
        <Col xs={24} sm={8}><Card><Statistic title="Critical rules" value={critical} prefix={<FireOutlined style={{ color: '#ef4444' }} />} /></Card></Col>
        <Col xs={24} sm={8}><Card><Statistic title="OWASP Top 10 categories" value={owasp} suffix="/ 10" /></Card></Col>
      </Row>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        title="Critical rules always win"
        description="A critical rule match is reported even when the ML layer disagrees, so known high-impact vulnerabilities are never suppressed."
      />

      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="Search rules, CWE…"
            style={{ width: 260 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Select
            allowClear
            placeholder="Severity"
            style={{ width: 160 }}
            value={severity}
            onChange={setSeverity}
            options={['critical', 'high', 'medium', 'low'].map((s) => ({ value: s, label: s[0].toUpperCase() + s.slice(1) }))}
          />
        </Space>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={filtered}
          columns={columns}
          pagination={false}
          scroll={{ x: 900 }}
          expandable={{
            expandedRowRender: (r) => (
              <Paragraph style={{ margin: 0 }}>
                <Text strong>Remediation: </Text>{r.remediation || '—'}
              </Paragraph>
            ),
          }}
        />
      </Card>
    </div>
  );
}
