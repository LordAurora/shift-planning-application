'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Tag,
  Space,
  Typography,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CodeOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  StopOutlined,
  SearchOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import {
  SecurityRule,
  SecurityRuleRequest,
  VulnerabilityCategory,
  VulnerabilitySeverity,
} from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// Severity and category options
const severityOptions: VulnerabilitySeverity[] = ['critical', 'high', 'medium', 'low', 'info'];
const categoryOptions: { value: VulnerabilityCategory; label: string; cwe: string }[] = [
  { value: 'sql_injection', label: 'SQL Injection', cwe: 'CWE-89' },
  { value: 'command_injection', label: 'Command Injection', cwe: 'CWE-78' },
  { value: 'path_traversal', label: 'Path Traversal', cwe: 'CWE-22' },
  { value: 'xss', label: 'Cross-Site Scripting (XSS)', cwe: 'CWE-79' },
  { value: 'hardcoded_secret', label: 'Hardcoded Secret', cwe: 'CWE-798' },
  { value: 'weak_crypto', label: 'Weak Cryptography', cwe: 'CWE-327' },
  { value: 'auth_bypass', label: 'Authentication Bypass', cwe: 'CWE-287' },
  { value: 'insecure_config', label: 'Insecure Configuration', cwe: 'CWE-16' },
  { value: 'access_control', label: 'Access Control Issue', cwe: 'CWE-284' },
  { value: 'data_exposure', label: 'Data Exposure', cwe: 'CWE-200' },
  { value: 'other', label: 'Other', cwe: 'N/A' },
];

const severityColors: Record<VulnerabilitySeverity, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'green',
  info: 'blue',
};

// Mock rules data
const mockRules: SecurityRule[] = [
  {
    id: 'rule-001',
    name: 'SQL String Concatenation',
    description: 'Detects SQL queries built using string concatenation, which may lead to SQL injection.',
    category: 'sql_injection',
    severity: 'critical',
    pattern: '(execute|query)\\s*\\(\\s*["\'].*\\+.*["\']',
    pattern_type: 'regex',
    cwe_id: 'CWE-89',
    owasp_category: 'A03:2021-Injection',
    is_active: true,
    false_positive_rate: 0.02,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T14:30:00Z',
  },
  {
    id: 'rule-002',
    name: 'Hardcoded API Key Pattern',
    description: 'Detects hardcoded API keys and secrets in source code.',
    category: 'hardcoded_secret',
    severity: 'high',
    pattern: '(api[_-]?key|secret|password)\\s*=\\s*["\'][a-zA-Z0-9]{16,}["\']',
    pattern_type: 'regex',
    cwe_id: 'CWE-798',
    owasp_category: 'A07:2021-Identification and Authentication Failures',
    is_active: true,
    false_positive_rate: 0.05,
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-18T11:00:00Z',
  },
  {
    id: 'rule-003',
    name: 'OS Command Execution',
    description: 'Detects potential command injection via os.system or subprocess with user input.',
    category: 'command_injection',
    severity: 'critical',
    pattern: '(os\\.system|subprocess\\.(call|run|Popen))\\s*\\([^)]*\\+',
    pattern_type: 'regex',
    cwe_id: 'CWE-78',
    owasp_category: 'A03:2021-Injection',
    is_active: true,
    false_positive_rate: 0.03,
    created_at: '2024-01-12T08:00:00Z',
    updated_at: '2024-01-12T08:00:00Z',
  },
  {
    id: 'rule-004',
    name: 'Path Traversal Pattern',
    description: 'Detects file operations that may be vulnerable to path traversal attacks.',
    category: 'path_traversal',
    severity: 'high',
    pattern: 'open\\s*\\([^)]*\\+[^)]*\\)',
    pattern_type: 'regex',
    cwe_id: 'CWE-22',
    owasp_category: 'A01:2021-Broken Access Control',
    is_active: true,
    false_positive_rate: 0.08,
    created_at: '2024-01-14T16:00:00Z',
    updated_at: '2024-01-19T10:00:00Z',
  },
  {
    id: 'rule-005',
    name: 'Weak Hash Algorithm',
    description: 'Detects usage of weak or deprecated hash algorithms (MD5, SHA1).',
    category: 'weak_crypto',
    severity: 'medium',
    pattern: '(hashlib\\.(md5|sha1)|MD5|SHA1)\\s*\\(',
    pattern_type: 'regex',
    cwe_id: 'CWE-327',
    owasp_category: 'A02:2021-Cryptographic Failures',
    is_active: false,
    false_positive_rate: 0.15,
    created_at: '2024-01-08T12:00:00Z',
    updated_at: '2024-01-16T09:00:00Z',
  },
];

export default function SecurityRulesPage() {
  const [rules, setRules] = useState<SecurityRule[]>(mockRules);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<SecurityRule | null>(null);
  const [form] = Form.useForm();
  const [testForm] = Form.useForm();
  const [testResult, setTestResult] = useState<{ matches: string[]; count: number } | null>(null);
  const [searchText, setSearchText] = useState('');

  // Filter rules based on search
  const filteredRules = rules.filter(
    rule =>
      rule.name.toLowerCase().includes(searchText.toLowerCase()) ||
      rule.description.toLowerCase().includes(searchText.toLowerCase()) ||
      rule.category.toLowerCase().includes(searchText.toLowerCase())
  );

  // Stats
  const activeRules = rules.filter(r => r.is_active).length;
  const criticalRules = rules.filter(r => r.severity === 'critical').length;
  const avgFalsePositive = rules.reduce((acc, r) => acc + (r.false_positive_rate || 0), 0) / rules.length;

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (rule: SecurityRule) => {
    setEditingRule(rule);
    form.setFieldsValue(rule);
    setModalVisible(true);
  };

  const handleDelete = async (ruleId: string) => {
    setLoading(true);
    try {
      // TODO: API call
      await new Promise(resolve => setTimeout(resolve, 500));
      setRules(rules.filter(r => r.id !== ruleId));
      message.success('Rule deleted successfully');
    } catch (error) {
      message.error('Failed to delete rule');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (ruleId: string, isActive: boolean) => {
    try {
      // TODO: API call
      await new Promise(resolve => setTimeout(resolve, 300));
      setRules(rules.map(r => (r.id === ruleId ? { ...r, is_active: isActive } : r)));
      message.success(`Rule ${isActive ? 'activated' : 'deactivated'}`);
    } catch (error) {
      message.error('Failed to update rule status');
    }
  };

  const handleSubmit = async (values: SecurityRuleRequest) => {
    setLoading(true);
    try {
      // TODO: API call
      await new Promise(resolve => setTimeout(resolve, 500));

      if (editingRule) {
        setRules(
          rules.map(r =>
            r.id === editingRule.id
              ? { ...r, ...values, updated_at: new Date().toISOString() }
              : r
          )
        );
        message.success('Rule updated successfully');
      } else {
        const newRule: SecurityRule = {
          ...values,
          id: `rule-${Date.now()}`,
          false_positive_rate: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setRules([...rules, newRule]);
        message.success('Rule created successfully');
      }

      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('Failed to save rule');
    } finally {
      setLoading(false);
    }
  };

  const handleTestRule = async (values: { pattern: string; pattern_type: string; sample_code: string }) => {
    try {
      // Simulate rule testing
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock test result
      const regex = new RegExp(values.pattern, 'gi');
      const matches = values.sample_code.match(regex) || [];

      setTestResult({
        matches,
        count: matches.length,
      });
    } catch (error) {
      message.error('Invalid pattern or test failed');
      setTestResult(null);
    }
  };

  const columns = [
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean, record: SecurityRule) => (
        <Switch
          checked={isActive}
          onChange={checked => handleToggleActive(record.id, checked)}
          checkedChildren={<CheckCircleOutlined />}
          unCheckedChildren={<StopOutlined />}
        />
      ),
    },
    {
      title: 'Rule Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: SecurityRule) => (
        <div>
          <Text strong>{name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.description.substring(0, 60)}...
          </Text>
        </div>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: VulnerabilityCategory) => {
        const cat = categoryOptions.find(c => c.value === category);
        return (
          <Tooltip title={cat?.cwe}>
            <Tag>{cat?.label || category}</Tag>
          </Tooltip>
        );
      },
    },
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
      title: 'Pattern Type',
      dataIndex: 'pattern_type',
      key: 'pattern_type',
      width: 100,
      render: (type: string) => <Tag color="blue">{type.toUpperCase()}</Tag>,
    },
    {
      title: 'FP Rate',
      dataIndex: 'false_positive_rate',
      key: 'false_positive_rate',
      width: 80,
      render: (rate: number) => (
        <Text style={{ color: rate > 0.1 ? '#ff4d4f' : rate > 0.05 ? '#faad14' : '#52c41a' }}>
          {((rate || 0) * 100).toFixed(1)}%
        </Text>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: SecurityRule) => (
        <Space>
          <Tooltip title="Edit Rule">
            <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
          </Tooltip>
          <Tooltip title="Test Rule">
            <Button
              icon={<ExperimentOutlined />}
              size="small"
              onClick={() => {
                testForm.setFieldsValue({
                  pattern: record.pattern,
                  pattern_type: record.pattern_type,
                });
                setTestModalVisible(true);
              }}
            />
          </Tooltip>
          <Popconfirm
            title="Delete this rule?"
            description="This action cannot be undone."
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            cancelText="Cancel"
            okButtonProps={{ danger: true }}
          >
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <CodeOutlined style={{ marginRight: 12 }} />
          Security Detection Rules
        </Title>
        <Text type="secondary">
          Manage rule-based detection patterns for deterministic vulnerability detection
        </Text>
      </div>

      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Rules"
              value={rules.length}
              prefix={<CodeOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Active Rules"
              value={activeRules}
              suffix={`/ ${rules.length}`}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Avg False Positive Rate"
              value={(avgFalsePositive * 100).toFixed(1)}
              suffix="%"
              prefix={
                avgFalsePositive > 0.1 ? (
                  <StopOutlined style={{ color: '#ff4d4f' }} />
                ) : (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                )
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Alert about rule priority */}
      <Alert
        message="Rule-Based Detection Priority"
        description="Critical and high severity rules take precedence in the hybrid engine. Rules with pattern_type='regex' are fastest, while 'ast' and 'semantic' provide deeper analysis."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
        closable
      />

      {/* Actions Bar */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Input
              placeholder="Search rules..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              style={{ width: 300 }}
              allowClear
            />
          </Col>
          <Col>
            <Space>
              <Button
                icon={<ExperimentOutlined />}
                onClick={() => {
                  testForm.resetFields();
                  setTestResult(null);
                  setTestModalVisible(true);
                }}
              >
                Test Pattern
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                Add Rule
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Rules Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredRules}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showSizeChanger: true }}
          expandable={{
            expandedRowRender: record => (
              <div style={{ padding: '12px 0' }}>
                <Paragraph>
                  <Text strong>Pattern: </Text>
                  <Text code style={{ wordBreak: 'break-all' }}>
                    {record.pattern}
                  </Text>
                </Paragraph>
                <Paragraph>
                  <Text strong>CWE: </Text>
                  <Tag>{record.cwe_id}</Tag>
                  <Text strong style={{ marginLeft: 16 }}>OWASP: </Text>
                  <Tag>{record.owasp_category}</Tag>
                </Paragraph>
                <Paragraph>
                  <Text strong>Last Updated: </Text>
                  <Text type="secondary">{new Date(record.updated_at).toLocaleString()}</Text>
                </Paragraph>
              </div>
            ),
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingRule ? 'Edit Security Rule' : 'Create Security Rule'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="Rule Name" rules={[{ required: true, message: 'Please enter rule name' }]}>
            <Input placeholder="e.g., SQL String Concatenation" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea rows={2} placeholder="Describe what this rule detects..." />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="category"
                label="Category"
                rules={[{ required: true, message: 'Please select category' }]}
              >
                <Select placeholder="Select category">
                  {categoryOptions.map(cat => (
                    <Option key={cat.value} value={cat.value}>
                      {cat.label} ({cat.cwe})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="severity"
                label="Severity"
                rules={[{ required: true, message: 'Please select severity' }]}
              >
                <Select placeholder="Select severity">
                  {severityOptions.map(sev => (
                    <Option key={sev} value={sev}>
                      <Tag color={severityColors[sev]}>{sev.toUpperCase()}</Tag>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="pattern"
            label="Detection Pattern"
            rules={[{ required: true, message: 'Please enter pattern' }]}
          >
            <TextArea
              rows={3}
              placeholder="Enter regex or pattern..."
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="pattern_type"
                label="Pattern Type"
                rules={[{ required: true, message: 'Please select type' }]}
              >
                <Select placeholder="Select type">
                  <Option value="regex">Regex (Fast)</Option>
                  <Option value="ast">AST (Deep)</Option>
                  <Option value="semantic">Semantic (Context-aware)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_active" label="Status" valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="cwe_id" label="CWE ID">
                <Input placeholder="e.g., CWE-89" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="owasp_category" label="OWASP Category">
                <Input placeholder="e.g., A03:2021-Injection" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                {editingRule ? 'Update Rule' : 'Create Rule'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Test Pattern Modal */}
      <Modal
        title="Test Detection Pattern"
        open={testModalVisible}
        onCancel={() => {
          setTestModalVisible(false);
          setTestResult(null);
        }}
        footer={null}
        width={700}
      >
        <Form form={testForm} layout="vertical" onFinish={handleTestRule}>
          <Form.Item name="pattern" label="Pattern" rules={[{ required: true }]}>
            <TextArea rows={2} style={{ fontFamily: 'monospace' }} placeholder="Enter regex pattern..." />
          </Form.Item>

          <Form.Item name="pattern_type" label="Pattern Type" initialValue="regex">
            <Select>
              <Option value="regex">Regex</Option>
              <Option value="ast">AST</Option>
            </Select>
          </Form.Item>

          <Form.Item name="sample_code" label="Sample Code to Test" rules={[{ required: true }]}>
            <TextArea
              rows={6}
              style={{ fontFamily: 'monospace' }}
              placeholder="Paste code to test the pattern against..."
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />} block>
              Run Test
            </Button>
          </Form.Item>
        </Form>

        {testResult && (
          <Alert
            message={`Found ${testResult.count} match${testResult.count !== 1 ? 'es' : ''}`}
            description={
              testResult.count > 0 ? (
                <div>
                  <Text strong>Matches:</Text>
                  <ul style={{ marginTop: 8 }}>
                    {testResult.matches.map((match, i) => (
                      <li key={i}>
                        <Text code>{match}</Text>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                'No matches found in the sample code.'
              )
            }
            type={testResult.count > 0 ? 'success' : 'warning'}
            showIcon
          />
        )}
      </Modal>
    </div>
  );
}
