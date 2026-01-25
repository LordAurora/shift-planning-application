'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Steps,
  Progress,
  Typography,
  Space,
  Alert,
  Spin,
  Button,
  Tag,
  Timeline,
  Collapse,
  Divider,
  List,
  Tooltip,
  Badge,
} from 'antd';
import {
  CloudServerOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  DatabaseOutlined,
  CodeOutlined,
  ApiOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { MigrationStatus } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

// Mock migration status
const mockMigrationStatus: MigrationStatus = {
  phase: 'preparing',
  components: [
    { name: 'Dataset Schema', status: 'completed', progress_percent: 100, notes: 'Schema is cloud-agnostic, ready for OBS' },
    { name: 'Labels & Taxonomy', status: 'completed', progress_percent: 100, notes: 'CWE/OWASP aligned labels unchanged' },
    { name: 'Security Rules', status: 'completed', progress_percent: 100, notes: 'Rule definitions portable to MindSpore' },
    { name: 'Feature Extraction', status: 'completed', progress_percent: 100, notes: 'Using framework-agnostic operations' },
    { name: 'Model Architecture', status: 'in_progress', progress_percent: 65, notes: 'Converting TF ops to MindSpore nn.Cell' },
    { name: 'Training Loop', status: 'in_progress', progress_percent: 40, notes: 'Adapting to Model.train() API' },
    { name: 'Loss Functions', status: 'not_started', progress_percent: 0, notes: 'Focal Loss needs MindSpore port' },
    { name: 'Inference API', status: 'not_started', progress_percent: 0, notes: 'Design ready, implementation pending' },
    { name: 'Ascend NPU Optimization', status: 'not_started', progress_percent: 0, notes: 'Graph mode & mixed precision planned' },
  ],
  target_platform: 'huawei_modelarts',
  estimated_completion: '2024-Q2',
  blockers: [
    'MindSpore 2.x API stabilization pending',
    'Ascend driver version compatibility testing needed',
  ],
  last_updated: new Date().toISOString(),
};

// Migration checklist items
const migrationChecklist = {
  dataset: [
    { id: 'd1', title: 'Dataset directory structure defined', status: 'completed' },
    { id: 'd2', title: 'Sample-level schema documented', status: 'completed' },
    { id: 'd3', title: 'Label taxonomy (CWE/OWASP) aligned', status: 'completed' },
    { id: 'd4', title: 'Metadata for FP/FN tracking', status: 'completed' },
    { id: 'd5', title: 'OBS bucket configuration ready', status: 'pending' },
  ],
  model: [
    { id: 'm1', title: 'Architecture documented', status: 'completed' },
    { id: 'm2', title: 'TensorFlow-only ops identified', status: 'completed' },
    { id: 'm3', title: 'nn.Cell wrapper classes created', status: 'in_progress' },
    { id: 'm4', title: 'Weight initialization ported', status: 'pending' },
    { id: 'm5', title: 'Checkpoint format conversion', status: 'pending' },
  ],
  training: [
    { id: 't1', title: 'Training loop redesign (Model.train)', status: 'in_progress' },
    { id: 't2', title: 'Loss function MindSpore port', status: 'pending' },
    { id: 't3', title: 'Optimizer configuration', status: 'pending' },
    { id: 't4', title: 'LR scheduler adaptation', status: 'pending' },
    { id: 't5', title: 'Early stopping callback', status: 'pending' },
  ],
  inference: [
    { id: 'i1', title: 'Secure API design (TLS, API key)', status: 'completed' },
    { id: 'i2', title: 'Rate limiting implementation', status: 'pending' },
    { id: 'i3', title: 'VPC isolation configuration', status: 'pending' },
    { id: 'i4', title: 'ModelArts deployment config', status: 'pending' },
  ],
  infrastructure: [
    { id: 'inf1', title: 'Ascend NPU compatibility check', status: 'pending' },
    { id: 'inf2', title: 'Graph mode optimization', status: 'pending' },
    { id: 'inf3', title: 'Mixed precision (O2) setup', status: 'pending' },
    { id: 'inf4', title: 'Data sink mode configuration', status: 'pending' },
    { id: 'inf5', title: 'Gradient checkpointing', status: 'pending' },
  ],
};

export default function MigrationStatusPage() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<MigrationStatus | null>(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 800));
      setStatus(mockMigrationStatus);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'in_progress':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'blocked':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getPhaseStep = (phase: string) => {
    switch (phase) {
      case 'local':
        return 0;
      case 'preparing':
        return 1;
      case 'migrating':
        return 2;
      case 'cloud':
        return 3;
      default:
        return 0;
    }
  };

  const overallProgress = status
    ? Math.round(
        status.components.reduce((acc, c) => acc + c.progress_percent, 0) / status.components.length
      )
    : 0;

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" tip="Loading migration status..." />
      </div>
    );
  }

  if (!status) return null;

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <CloudServerOutlined style={{ marginRight: 12 }} />
            Huawei Cloud Migration Status
          </Title>
          <Text type="secondary">
            TensorFlow → MindSpore / ModelArts migration progress
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadStatus}>
            Refresh
          </Button>
          <Button type="primary" icon={<FileTextOutlined />}>
            Export Report
          </Button>
        </Space>
      </div>

      {/* Migration Phase */}
      <Card style={{ marginBottom: 24 }}>
        <Steps 
          current={getPhaseStep(status.phase)} 
          style={{ marginBottom: 24 }}
          items={[
            {
              title: 'Local Development',
              description: 'TensorFlow training',
              icon: <CodeOutlined />,
            },
            {
              title: 'Preparation',
              description: 'MindSpore adaptation',
              icon: <SettingOutlined />,
            },
            {
              title: 'Migration',
              description: 'Cloud deployment',
              icon: <CloudUploadOutlined />,
            },
            {
              title: 'Production',
              description: 'ModelArts serving',
              icon: <RocketOutlined />,
            },
          ]}
        />

        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={overallProgress}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                size={120}
              />
              <div style={{ marginTop: 12 }}>
                <Text strong>Overall Progress</Text>
              </div>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small">
              <Statistic
                title="Target Platform"
                value="Huawei ModelArts"
                prefix={<CloudServerOutlined />}
              />
              <Divider style={{ margin: '12px 0' }} />
              <Text type="secondary">Framework: MindSpore 2.x</Text>
              <br />
              <Text type="secondary">Hardware: Ascend NPU</Text>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small">
              <Statistic
                title="Estimated Completion"
                value={status.estimated_completion || 'TBD'}
                prefix={<ClockCircleOutlined />}
              />
              <Divider style={{ margin: '12px 0' }} />
              <Text type="secondary">
                Last Updated: {new Date(status.last_updated).toLocaleDateString()}
              </Text>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* Blockers */}
      {status.blockers.length > 0 && (
        <Alert
          message="Migration Blockers"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {status.blockers.map((blocker, index) => (
                <li key={index}>{blocker}</li>
              ))}
            </ul>
          }
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Component Progress */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Component Migration Status">
            <Row gutter={[16, 16]}>
              {status.components.map(component => (
                <Col xs={24} sm={12} lg={8} key={component.name}>
                  <Card size="small" style={{ height: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <Text strong>{component.name}</Text>
                      {getStatusIcon(component.status)}
                    </div>
                    <Progress
                      percent={component.progress_percent}
                      size="small"
                      status={
                        component.status === 'completed'
                          ? 'success'
                          : component.status === 'blocked'
                          ? 'exception'
                          : 'active'
                      }
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {component.notes}
                    </Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Detailed Checklist */}
      <Card title="Migration Checklist">
        <Collapse defaultActiveKey={['dataset', 'model']}>
          <Panel
            header={
              <Space>
                <DatabaseOutlined />
                <span>Dataset & Labels</span>
                <Badge
                  count={migrationChecklist.dataset.filter(i => i.status === 'completed').length}
                  style={{ backgroundColor: '#52c41a' }}
                />
                <span style={{ color: '#8c8c8c' }}>/ {migrationChecklist.dataset.length}</span>
              </Space>
            }
            key="dataset"
          >
            <List
              size="small"
              dataSource={migrationChecklist.dataset}
              renderItem={item => (
                <List.Item>
                  <Space>
                    {getStatusIcon(item.status)}
                    <Text delete={item.status === 'completed'}>{item.title}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Panel>

          <Panel
            header={
              <Space>
                <CodeOutlined />
                <span>Model Architecture</span>
                <Badge
                  count={migrationChecklist.model.filter(i => i.status === 'completed').length}
                  style={{ backgroundColor: '#52c41a' }}
                />
                <span style={{ color: '#8c8c8c' }}>/ {migrationChecklist.model.length}</span>
              </Space>
            }
            key="model"
          >
            <List
              size="small"
              dataSource={migrationChecklist.model}
              renderItem={item => (
                <List.Item>
                  <Space>
                    {getStatusIcon(item.status)}
                    <Text delete={item.status === 'completed'}>{item.title}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Panel>

          <Panel
            header={
              <Space>
                <ThunderboltOutlined />
                <span>Training Pipeline</span>
                <Badge
                  count={migrationChecklist.training.filter(i => i.status === 'completed').length}
                  style={{ backgroundColor: '#52c41a' }}
                />
                <span style={{ color: '#8c8c8c' }}>/ {migrationChecklist.training.length}</span>
              </Space>
            }
            key="training"
          >
            <List
              size="small"
              dataSource={migrationChecklist.training}
              renderItem={item => (
                <List.Item>
                  <Space>
                    {getStatusIcon(item.status)}
                    <Text delete={item.status === 'completed'}>{item.title}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Panel>

          <Panel
            header={
              <Space>
                <ApiOutlined />
                <span>Inference API</span>
                <Badge
                  count={migrationChecklist.inference.filter(i => i.status === 'completed').length}
                  style={{ backgroundColor: '#52c41a' }}
                />
                <span style={{ color: '#8c8c8c' }}>/ {migrationChecklist.inference.length}</span>
              </Space>
            }
            key="inference"
          >
            <List
              size="small"
              dataSource={migrationChecklist.inference}
              renderItem={item => (
                <List.Item>
                  <Space>
                    {getStatusIcon(item.status)}
                    <Text delete={item.status === 'completed'}>{item.title}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Panel>

          <Panel
            header={
              <Space>
                <SafetyCertificateOutlined />
                <span>Ascend NPU Optimization</span>
                <Badge
                  count={migrationChecklist.infrastructure.filter(i => i.status === 'completed').length}
                  style={{ backgroundColor: '#52c41a' }}
                />
                <span style={{ color: '#8c8c8c' }}>/ {migrationChecklist.infrastructure.length}</span>
              </Space>
            }
            key="infrastructure"
          >
            <List
              size="small"
              dataSource={migrationChecklist.infrastructure}
              renderItem={item => (
                <List.Item>
                  <Space>
                    {getStatusIcon(item.status)}
                    <Text delete={item.status === 'completed'}>{item.title}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Panel>
        </Collapse>
      </Card>

      {/* What Changes vs What Stays */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <span>Unchanged (Portable)</span>
              </Space>
            }
          >
            <Timeline>
              <Timeline.Item color="green">Dataset schema & directory structure</Timeline.Item>
              <Timeline.Item color="green">Label taxonomy (CWE/OWASP)</Timeline.Item>
              <Timeline.Item color="green">Security detection rules</Timeline.Item>
              <Timeline.Item color="green">Evaluation metrics logic</Timeline.Item>
              <Timeline.Item color="green">Continuous learning workflow</Timeline.Item>
              <Timeline.Item color="green">API interface contracts</Timeline.Item>
            </Timeline>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <SyncOutlined style={{ color: '#1890ff' }} />
                <span>Requires Migration</span>
              </Space>
            }
          >
            <Timeline>
              <Timeline.Item color="blue">Model definition (tf.keras → nn.Cell)</Timeline.Item>
              <Timeline.Item color="blue">Training loop (fit → Model.train)</Timeline.Item>
              <Timeline.Item color="blue">Data pipeline (tf.data → MindData)</Timeline.Item>
              <Timeline.Item color="blue">Loss/Optimizer syntax</Timeline.Item>
              <Timeline.Item color="blue">Checkpoint format</Timeline.Item>
              <Timeline.Item color="blue">Distributed training config</Timeline.Item>
            </Timeline>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

// Helper component for statistics
function Statistic({ title, value, prefix }: { title: string; value: string; prefix: React.ReactNode }) {
  return (
    <div>
      <Text type="secondary" style={{ fontSize: 12 }}>
        {title}
      </Text>
      <div style={{ fontSize: 20, fontWeight: 600, marginTop: 4 }}>
        {prefix && <span style={{ marginRight: 8 }}>{prefix}</span>}
        {value}
      </div>
    </div>
  );
}
