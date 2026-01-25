'use client';

import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Typography,
  Space,
  Alert,
  Spin,
  Button,
  Tooltip,
} from 'antd';
import {
  SecurityScanOutlined,
  BugOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  RobotOutlined,
  CodeOutlined,
  CloudServerOutlined,
  ReloadOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import {
  SecurityDashboardStats,
  SecurityScanResult,
  Vulnerability,
  VulnerabilitySeverity,
} from '../types';

const { Title, Text } = Typography;

// Mock data for initial development (will be replaced with API calls)
const mockDashboardStats: SecurityDashboardStats = {
  total_scans: 47,
  total_vulnerabilities: 156,
  open_vulnerabilities: 23,
  resolved_vulnerabilities: 133,
  severity_distribution: {
    critical: 3,
    high: 8,
    medium: 12,
    low: 67,
    info: 66,
  },
  category_distribution: {
    sql_injection: 5,
    command_injection: 2,
    path_traversal: 4,
    xss: 8,
    hardcoded_secret: 12,
    weak_crypto: 6,
    auth_bypass: 3,
    insecure_config: 15,
    access_control: 7,
    data_exposure: 9,
    other: 85,
  },
  detection_source_distribution: {
    rule: 89,
    ml: 42,
    hybrid: 25,
  },
  recent_scans: [],
  top_vulnerabilities: [],
  model_accuracy: 94.7,
  false_positive_rate: 3.2,
};

const severityColors: Record<VulnerabilitySeverity, string> = {
  critical: '#ff4d4f',
  high: '#fa8c16',
  medium: '#faad14',
  low: '#52c41a',
  info: '#1890ff',
};

const severityOrder: VulnerabilitySeverity[] = ['critical', 'high', 'medium', 'low', 'info'];

export default function SecurityDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<SecurityDashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // TODO: Replace with actual API call
      // const data = await securityScanService.getDashboardStats();
      await new Promise(resolve => setTimeout(resolve, 800)); // Simulate API delay
      setStats(mockDashboardStats);
    } catch (err) {
      setError('Failed to load security dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" tip="Loading security dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
        action={
          <Button onClick={loadDashboardData} size="small">
            Retry
          </Button>
        }
      />
    );
  }

  if (!stats) return null;

  const totalSeverity = Object.values(stats.severity_distribution).reduce((a, b) => a + b, 0);

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <SecurityScanOutlined style={{ marginRight: 12 }} />
            Security AI Dashboard
          </Title>
          <Text type="secondary">
            Hybrid security analysis powered by Rule Engine + Machine Learning
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadDashboardData}>
            Refresh
          </Button>
          <Button type="primary" icon={<SecurityScanOutlined />} onClick={() => router.push('/security/scan')}>
            New Scan
          </Button>
        </Space>
      </div>

      {/* Quick Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Scans"
              value={stats.total_scans}
              prefix={<SecurityScanOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Open Vulnerabilities"
              value={stats.open_vulnerabilities}
              prefix={<BugOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: stats.open_vulnerabilities > 10 ? '#ff4d4f' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Model Accuracy"
              value={stats.model_accuracy}
              suffix="%"
              prefix={<RobotOutlined style={{ color: '#52c41a' }} />}
              precision={1}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="False Positive Rate"
              value={stats.false_positive_rate}
              suffix="%"
              prefix={<WarningOutlined style={{ color: stats.false_positive_rate > 5 ? '#faad14' : '#52c41a' }} />}
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* Severity Distribution & Detection Sources */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <BugOutlined />
                <span>Vulnerability Severity Distribution</span>
              </Space>
            }
            extra={
              <Button type="link" onClick={() => router.push('/security/vulnerabilities')}>
                View All <RightOutlined />
              </Button>
            }
          >
            <div style={{ padding: '8px 0' }}>
              {severityOrder.map(severity => {
                const count = stats.severity_distribution[severity];
                const percent = totalSeverity > 0 ? (count / totalSeverity) * 100 : 0;
                return (
                  <div key={severity} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <Tag color={severityColors[severity]} style={{ textTransform: 'uppercase' }}>
                        {severity}
                      </Tag>
                      <Text strong>{count}</Text>
                    </div>
                    <Progress
                      percent={percent}
                      showInfo={false}
                      strokeColor={severityColors[severity]}
                      size="small"
                    />
                  </div>
                );
              })}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <RobotOutlined />
                <span>Detection Source Analysis</span>
              </Space>
            }
            extra={
              <Tooltip title="Hybrid Engine combines Rule-based and ML detection">
                <Button type="link">Learn More</Button>
              </Tooltip>
            }
          >
            <Row gutter={[16, 16]} style={{ padding: '16px 0' }}>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={Math.round((stats.detection_source_distribution.rule / stats.total_vulnerabilities) * 100)}
                    strokeColor="#1890ff"
                    size={80}
                  />
                  <div style={{ marginTop: 8 }}>
                    <Text strong>Rule-Based</Text>
                    <br />
                    <Text type="secondary">{stats.detection_source_distribution.rule} detections</Text>
                  </div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={Math.round((stats.detection_source_distribution.ml / stats.total_vulnerabilities) * 100)}
                    strokeColor="#722ed1"
                    size={80}
                  />
                  <div style={{ marginTop: 8 }}>
                    <Text strong>ML-Based</Text>
                    <br />
                    <Text type="secondary">{stats.detection_source_distribution.ml} detections</Text>
                  </div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress
                    type="circle"
                    percent={Math.round((stats.detection_source_distribution.hybrid / stats.total_vulnerabilities) * 100)}
                    strokeColor="#13c2c2"
                    size={80}
                  />
                  <div style={{ marginTop: 8 }}>
                    <Text strong>Hybrid</Text>
                    <br />
                    <Text type="secondary">{stats.detection_source_distribution.hybrid} detections</Text>
                  </div>
                </div>
              </Col>
            </Row>

            <Alert
              message="Hybrid Detection Active"
              description="The system uses a fusion strategy combining deterministic rules for critical vulnerabilities with ML for pattern detection."
              type="info"
              showIcon
              icon={<CheckCircleOutlined />}
              style={{ marginTop: 16 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            onClick={() => router.push('/security/scan')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <SecurityScanOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
            <Title level={5}>Run Security Scan</Title>
            <Text type="secondary">Analyze code with hybrid engine</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            onClick={() => router.push('/security/rules')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <CodeOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 8 }} />
            <Title level={5}>Security Rules</Title>
            <Text type="secondary">Manage detection rules</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            onClick={() => router.push('/security/training')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <RobotOutlined style={{ fontSize: 32, color: '#722ed1', marginBottom: 8 }} />
            <Title level={5}>ML Training</Title>
            <Text type="secondary">Model training & evaluation</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            onClick={() => router.push('/security/migration')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <CloudServerOutlined style={{ fontSize: 32, color: '#fa8c16', marginBottom: 8 }} />
            <Title level={5}>Huawei Migration</Title>
            <Text type="secondary">ModelArts & MindSpore status</Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
