'use client';

import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  Select,
  Button,
  Typography,
  Space,
  Alert,
  Spin,
  Tabs,
  Table,
  Tag,
  Collapse,
  Tooltip,
  message,
  Divider,
} from 'antd';
import {
  SecurityScanOutlined,
  CodeOutlined,
  FileSearchOutlined,
  ApiOutlined,
  PlayCircleOutlined,
  BugOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CopyOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import {
  SecurityScanRequest,
  SecurityScanResult,
  Vulnerability,
  VulnerabilitySeverity,
} from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { Panel } = Collapse;

// Severity colors
const severityColors: Record<VulnerabilitySeverity, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'green',
  info: 'blue',
};

// Sample vulnerable code for demo
const sampleCodes = {
  sql_injection: `# SQL Injection Example
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()`,
  
  command_injection: `# Command Injection Example
import os

def process_file(filename):
    os.system("cat " + filename)
    return True`,
  
  hardcoded_secret: `# Hardcoded Secret Example
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

def connect_db():
    return psycopg2.connect(password=DB_PASSWORD)`,
  
  path_traversal: `# Path Traversal Example
def read_file(filename):
    path = "/var/data/" + filename
    with open(path, 'r') as f:
        return f.read()`,
};

// Mock scan result for demo
const mockScanResult: SecurityScanResult = {
  scan_id: 'scan-001',
  status: 'completed',
  scan_type: 'source_code',
  detection_mode: 'full',
  started_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
  duration_ms: 1250,
  vulnerabilities: [
    {
      id: 'vuln-001',
      category: 'sql_injection',
      severity: 'critical',
      title: 'SQL Injection Vulnerability',
      description: 'User input is directly concatenated into SQL query without sanitization.',
      file_path: 'app/database.py',
      line_number: 3,
      code_snippet: 'query = "SELECT * FROM users WHERE id = " + user_id',
      cwe_id: 'CWE-89',
      owasp_category: 'A03:2021-Injection',
      detection_source: 'rule',
      confidence_score: 0.98,
      mitigation: 'Use parameterized queries or prepared statements instead of string concatenation.',
      false_positive_flag: false,
      created_at: new Date().toISOString(),
    },
    {
      id: 'vuln-002',
      category: 'hardcoded_secret',
      severity: 'high',
      title: 'Hardcoded API Key',
      description: 'Sensitive API key found hardcoded in source code.',
      file_path: 'config.py',
      line_number: 2,
      code_snippet: 'API_KEY = "sk-1234567890abcdef"',
      cwe_id: 'CWE-798',
      owasp_category: 'A07:2021-Identification and Authentication Failures',
      detection_source: 'hybrid',
      confidence_score: 0.95,
      mitigation: 'Store secrets in environment variables or a secure secrets manager.',
      false_positive_flag: false,
      created_at: new Date().toISOString(),
    },
  ],
  summary: {
    total: 2,
    critical: 1,
    high: 1,
    medium: 0,
    low: 0,
    info: 0,
  },
  rule_detections: 1,
  ml_detections: 0,
  hybrid_detections: 1,
};

export default function SecurityScanPage() {
  const [form] = Form.useForm();
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<SecurityScanResult | null>(null);
  const [codeInput, setCodeInput] = useState('');

  const handleScan = async (values: SecurityScanRequest) => {
    setScanning(true);
    setScanResult(null);

    try {
      // TODO: Replace with actual API call
      // const result = await securityScanService.runScan(values);
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate scan
      setScanResult(mockScanResult);
      message.success('Security scan completed!');
    } catch (error) {
      message.error('Scan failed. Please try again.');
      console.error(error);
    } finally {
      setScanning(false);
    }
  };

  const loadSampleCode = (type: keyof typeof sampleCodes) => {
    setCodeInput(sampleCodes[type]);
    form.setFieldsValue({ content: sampleCodes[type] });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Copied to clipboard');
  };

  const vulnerabilityColumns = [
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: VulnerabilitySeverity) => (
        <Tag color={severityColors[severity]} style={{ textTransform: 'uppercase' }}>
          {severity}
        </Tag>
      ),
    },
    {
      title: 'Vulnerability',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: Vulnerability) => (
        <div>
          <Text strong>{title}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.cwe_id} | {record.owasp_category}
          </Text>
        </div>
      ),
    },
    {
      title: 'Location',
      key: 'location',
      render: (_: unknown, record: Vulnerability) => (
        <Text code>
          {record.file_path}:{record.line_number}
        </Text>
      ),
    },
    {
      title: 'Source',
      dataIndex: 'detection_source',
      key: 'detection_source',
      width: 100,
      render: (source: string) => {
        const colors: Record<string, string> = {
          rule: 'blue',
          ml: 'purple',
          hybrid: 'cyan',
        };
        return <Tag color={colors[source]}>{source.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      width: 100,
      render: (score: number) => (
        <Text strong style={{ color: score > 0.9 ? '#52c41a' : score > 0.7 ? '#faad14' : '#ff4d4f' }}>
          {(score * 100).toFixed(0)}%
        </Text>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <SecurityScanOutlined style={{ marginRight: 12 }} />
          Security Vulnerability Scanner
        </Title>
        <Text type="secondary">
          Analyze code for security vulnerabilities using hybrid detection (Rules + ML)
        </Text>
      </div>

      <Row gutter={[24, 24]}>
        {/* Scan Configuration */}
        <Col xs={24} lg={12}>
          <Card title="Scan Configuration" extra={<SecurityScanOutlined />}>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleScan}
              initialValues={{
                scan_type: 'source_code',
                detection_mode: 'full',
                include_mitigations: true,
              }}
            >
              <Form.Item name="scan_type" label="Scan Type">
                <Select>
                  <Option value="source_code">
                    <CodeOutlined /> Source Code Analysis
                  </Option>
                  <Option value="config">
                    <FileSearchOutlined /> Configuration Analysis
                  </Option>
                  <Option value="api">
                    <ApiOutlined /> API Security Analysis
                  </Option>
                  <Option value="full">
                    <SecurityScanOutlined /> Full Analysis
                  </Option>
                </Select>
              </Form.Item>

              <Form.Item name="detection_mode" label="Detection Mode">
                <Select>
                  <Option value="full">Full Hybrid (Rule + ML)</Option>
                  <Option value="rules_only">Rules Only (Deterministic)</Option>
                  <Option value="ml_only">ML Only (Pattern-based)</Option>
                  <Option value="critical_only">Critical Rules Only</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="content"
                label={
                  <Space>
                    <span>Code to Analyze</span>
                    <Tooltip title="Load sample vulnerable code for testing">
                      <Select
                        placeholder="Load sample"
                        size="small"
                        style={{ width: 150 }}
                        onChange={loadSampleCode}
                      >
                        <Option value="sql_injection">SQL Injection</Option>
                        <Option value="command_injection">Command Injection</Option>
                        <Option value="hardcoded_secret">Hardcoded Secret</Option>
                        <Option value="path_traversal">Path Traversal</Option>
                      </Select>
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true, message: 'Please enter code to analyze' }]}
              >
                <TextArea
                  rows={12}
                  placeholder="Paste your code here for security analysis..."
                  value={codeInput}
                  onChange={e => setCodeInput(e.target.value)}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<PlayCircleOutlined />}
                  loading={scanning}
                  size="large"
                  block
                >
                  {scanning ? 'Scanning...' : 'Run Security Scan'}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Scan Results */}
        <Col xs={24} lg={12}>
          <Card
            title="Scan Results"
            extra={
              scanResult && (
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(scanResult, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `security-scan-${scanResult.scan_id}.json`;
                    a.click();
                  }}
                >
                  Export
                </Button>
              )
            }
          >
            {scanning && (
              <div style={{ textAlign: 'center', padding: 48 }}>
                <Spin size="large" />
                <Title level={4} style={{ marginTop: 16 }}>
                  Analyzing code...
                </Title>
                <Text type="secondary">Running hybrid detection engine</Text>
              </div>
            )}

            {!scanning && !scanResult && (
              <div style={{ textAlign: 'center', padding: 48 }}>
                <SecurityScanOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                <Title level={4} style={{ marginTop: 16, color: '#8c8c8c' }}>
                  No Scan Results
                </Title>
                <Text type="secondary">Configure and run a scan to see results</Text>
              </div>
            )}

            {!scanning && scanResult && (
              <>
                {/* Summary */}
                <Alert
                  message={
                    scanResult.summary.critical > 0 || scanResult.summary.high > 0
                      ? 'Security Issues Found'
                      : 'Scan Complete'
                  }
                  description={
                    <Space direction="vertical" size={4}>
                      <Text>
                        Found <Text strong>{scanResult.summary.total}</Text> vulnerabilities
                      </Text>
                      <Text type="secondary">
                        Duration: {scanResult.duration_ms}ms | Mode: {scanResult.detection_mode}
                      </Text>
                    </Space>
                  }
                  type={scanResult.summary.critical > 0 ? 'error' : scanResult.summary.high > 0 ? 'warning' : 'success'}
                  showIcon
                  icon={scanResult.summary.critical > 0 ? <BugOutlined /> : <CheckCircleOutlined />}
                  style={{ marginBottom: 16 }}
                />

                {/* Severity Summary */}
                <Row gutter={8} style={{ marginBottom: 16 }}>
                  {(['critical', 'high', 'medium', 'low', 'info'] as VulnerabilitySeverity[]).map(severity => (
                    <Col key={severity}>
                      <Tag color={severityColors[severity]}>
                        {severity.toUpperCase()}: {scanResult.summary[severity]}
                      </Tag>
                    </Col>
                  ))}
                </Row>

                {/* Detection Source Stats */}
                <div style={{ marginBottom: 16 }}>
                  <Text type="secondary">Detection Sources: </Text>
                  <Tag color="blue">Rule: {scanResult.rule_detections}</Tag>
                  <Tag color="purple">ML: {scanResult.ml_detections}</Tag>
                  <Tag color="cyan">Hybrid: {scanResult.hybrid_detections}</Tag>
                </div>

                <Divider />

                {/* Vulnerabilities List */}
                <Collapse accordion>
                  {scanResult.vulnerabilities.map((vuln, index) => (
                    <Panel
                      key={vuln.id}
                      header={
                        <Space>
                          <Tag color={severityColors[vuln.severity]}>{vuln.severity.toUpperCase()}</Tag>
                          <Text strong>{vuln.title}</Text>
                        </Space>
                      }
                      extra={
                        <Tag color={vuln.detection_source === 'rule' ? 'blue' : vuln.detection_source === 'ml' ? 'purple' : 'cyan'}>
                          {vuln.detection_source}
                        </Tag>
                      }
                    >
                      <Paragraph>{vuln.description}</Paragraph>

                      <div style={{ marginBottom: 12 }}>
                        <Text strong>Location: </Text>
                        <Text code>{vuln.file_path}:{vuln.line_number}</Text>
                      </div>

                      {vuln.code_snippet && (
                        <div style={{ marginBottom: 12 }}>
                          <Text strong>Vulnerable Code:</Text>
                          <div
                            style={{
                              background: '#f5f5f5',
                              padding: 12,
                              borderRadius: 4,
                              fontFamily: 'monospace',
                              position: 'relative',
                            }}
                          >
                            <Button
                              icon={<CopyOutlined />}
                              size="small"
                              style={{ position: 'absolute', top: 8, right: 8 }}
                              onClick={() => copyToClipboard(vuln.code_snippet || '')}
                            />
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{vuln.code_snippet}</pre>
                          </div>
                        </div>
                      )}

                      <div style={{ marginBottom: 12 }}>
                        <Text strong>Reference: </Text>
                        <Tag>{vuln.cwe_id}</Tag>
                        <Tag>{vuln.owasp_category}</Tag>
                      </div>

                      <div style={{ marginBottom: 12 }}>
                        <Text strong>Confidence: </Text>
                        <Text style={{ color: vuln.confidence_score > 0.9 ? '#52c41a' : '#faad14' }}>
                          {(vuln.confidence_score * 100).toFixed(0)}%
                        </Text>
                      </div>

                      {vuln.mitigation && (
                        <Alert
                          message="Recommended Mitigation"
                          description={vuln.mitigation}
                          type="info"
                          showIcon
                          icon={<CheckCircleOutlined />}
                        />
                      )}
                    </Panel>
                  ))}
                </Collapse>
              </>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
