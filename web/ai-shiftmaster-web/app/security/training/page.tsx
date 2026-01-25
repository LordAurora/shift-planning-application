'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Button,
  Typography,
  Space,
  Alert,
  Spin,
  Modal,
  Form,
  InputNumber,
  Switch,
  Slider,
  Tabs,
  Tooltip,
  message,
  Timeline,
  Empty,
} from 'antd';
import {
  RobotOutlined,
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  LineChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  AimOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import {
  TrainingRun,
  TrainingConfig,
  TrainingMetrics,
  EvaluationResult,
  FeedbackRecord,
} from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// Mock training runs
const mockTrainingRuns: TrainingRun[] = [
  {
    id: 'train-003',
    status: 'completed',
    config: {
      epochs: 50,
      batch_size: 32,
      learning_rate: 0.001,
      early_stopping_patience: 5,
      class_weights_enabled: true,
      focal_loss_enabled: true,
      validation_split: 0.2,
    },
    started_at: '2024-01-20T10:00:00Z',
    completed_at: '2024-01-20T12:30:00Z',
    current_epoch: 50,
    total_epochs: 50,
    metrics: {
      accuracy: 0.947,
      precision: 0.932,
      recall: 0.958,
      f1_score: 0.945,
      false_positive_rate: 0.032,
      false_negative_rate: 0.042,
      mcc: 0.891,
      loss: 0.142,
      val_accuracy: 0.941,
      val_loss: 0.158,
    },
    best_checkpoint: 'model_epoch_47.h5',
  },
  {
    id: 'train-002',
    status: 'completed',
    config: {
      epochs: 30,
      batch_size: 64,
      learning_rate: 0.0005,
      early_stopping_patience: 3,
      class_weights_enabled: true,
      focal_loss_enabled: false,
      validation_split: 0.2,
    },
    started_at: '2024-01-18T14:00:00Z',
    completed_at: '2024-01-18T15:45:00Z',
    current_epoch: 30,
    total_epochs: 30,
    metrics: {
      accuracy: 0.923,
      precision: 0.915,
      recall: 0.931,
      f1_score: 0.923,
      false_positive_rate: 0.045,
      false_negative_rate: 0.069,
      mcc: 0.846,
      loss: 0.198,
      val_accuracy: 0.918,
      val_loss: 0.212,
    },
    best_checkpoint: 'model_epoch_28.h5',
  },
];

// Mock evaluation results
const mockEvaluations: EvaluationResult[] = [
  {
    id: 'eval-001',
    model_version: 'v1.3.0',
    evaluated_at: '2024-01-20T13:00:00Z',
    dataset_size: 5000,
    metrics: {
      accuracy: 0.947,
      precision: 0.932,
      recall: 0.958,
      f1_score: 0.945,
      false_positive_rate: 0.032,
      false_negative_rate: 0.042,
      loss: 0.142,
      class_metrics: {
        sql_injection: { precision: 0.98, recall: 0.99, f1_score: 0.985, support: 450 },
        command_injection: { precision: 0.96, recall: 0.97, f1_score: 0.965, support: 320 },
        hardcoded_secret: { precision: 0.94, recall: 0.96, f1_score: 0.95, support: 680 },
        path_traversal: { precision: 0.92, recall: 0.94, f1_score: 0.93, support: 280 },
        xss: { precision: 0.91, recall: 0.93, f1_score: 0.92, support: 520 },
        safe_code: { precision: 0.95, recall: 0.92, f1_score: 0.935, support: 2750 },
      },
    },
    confusion_matrix: [
      [445, 5],
      [12, 308],
    ],
    class_labels: ['vulnerable', 'safe'],
    threshold: 0.5,
    roc_auc: 0.978,
    pr_auc: 0.965,
  },
];

// Mock feedback records
const mockFeedback: FeedbackRecord[] = [
  {
    id: 'fb-001',
    vulnerability_id: 'vuln-123',
    feedback_type: 'false_positive',
    original_prediction: 'sql_injection',
    notes: 'This is a prepared statement, not vulnerable.',
    submitted_by: 'admin@example.com',
    submitted_at: '2024-01-19T10:30:00Z',
    used_in_retraining: false,
  },
  {
    id: 'fb-002',
    vulnerability_id: 'vuln-456',
    feedback_type: 'correct',
    original_prediction: 'hardcoded_secret',
    submitted_by: 'admin@example.com',
    submitted_at: '2024-01-18T14:20:00Z',
    used_in_retraining: true,
  },
];

export default function TrainingDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [trainingRuns, setTrainingRuns] = useState<TrainingRun[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationResult[]>([]);
  const [feedback, setFeedback] = useState<FeedbackRecord[]>([]);
  const [trainingModalVisible, setTrainingModalVisible] = useState(false);
  const [currentModelMetrics, setCurrentModelMetrics] = useState<TrainingMetrics | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API calls
      await new Promise(resolve => setTimeout(resolve, 800));
      setTrainingRuns(mockTrainingRuns);
      setEvaluations(mockEvaluations);
      setFeedback(mockFeedback);
      setCurrentModelMetrics(mockTrainingRuns[0]?.metrics || null);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTraining = async (values: TrainingConfig) => {
    try {
      // TODO: API call
      message.loading('Starting training...', 1);
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newRun: TrainingRun = {
        id: `train-${Date.now()}`,
        status: 'running',
        config: values,
        started_at: new Date().toISOString(),
        current_epoch: 0,
        total_epochs: values.epochs,
        metrics: {
          accuracy: 0,
          precision: 0,
          recall: 0,
          f1_score: 0,
          false_positive_rate: 0,
          false_negative_rate: 0,
          loss: 0,
        },
      };

      setTrainingRuns([newRun, ...trainingRuns]);
      setTrainingModalVisible(false);
      message.success('Training started successfully!');
    } catch (error) {
      message.error('Failed to start training');
    }
  };

  const getStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
      queued: { color: 'default', icon: <HistoryOutlined /> },
      running: { color: 'processing', icon: <PlayCircleOutlined spin /> },
      completed: { color: 'success', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', icon: <CloseCircleOutlined /> },
      cancelled: { color: 'warning', icon: <StopOutlined /> },
    };
    const config = statusConfig[status] || statusConfig.queued;
    return (
      <Tag color={config.color} icon={config.icon}>
        {status.toUpperCase()}
      </Tag>
    );
  };

  const trainingColumns = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Progress',
      key: 'progress',
      render: (_: unknown, record: TrainingRun) => (
        <Progress
          percent={Math.round((record.current_epoch || 0) / record.total_epochs * 100)}
          size="small"
          status={record.status === 'running' ? 'active' : undefined}
        />
      ),
    },
    {
      title: 'Accuracy',
      key: 'accuracy',
      render: (_: unknown, record: TrainingRun) => (
        <Text strong style={{ color: record.metrics.accuracy > 0.9 ? '#52c41a' : '#faad14' }}>
          {(record.metrics.accuracy * 100).toFixed(1)}%
        </Text>
      ),
    },
    {
      title: 'F1 Score',
      key: 'f1',
      render: (_: unknown, record: TrainingRun) => (
        <Text>{(record.metrics.f1_score * 100).toFixed(1)}%</Text>
      ),
    },
    {
      title: 'FPR',
      key: 'fpr',
      render: (_: unknown, record: TrainingRun) => (
        <Text style={{ color: record.metrics.false_positive_rate < 0.05 ? '#52c41a' : '#ff4d4f' }}>
          {(record.metrics.false_positive_rate * 100).toFixed(1)}%
        </Text>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" tip="Loading training data..." />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <RobotOutlined style={{ marginRight: 12 }} />
            ML Training & Evaluation
          </Title>
          <Text type="secondary">
            Train, evaluate, and improve the security ML model
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>
            Refresh
          </Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => setTrainingModalVisible(true)}>
            Start Training
          </Button>
        </Space>
      </div>

      {/* Current Model Stats */}
      {currentModelMetrics && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Model Accuracy"
                value={(currentModelMetrics.accuracy * 100).toFixed(1)}
                suffix="%"
                prefix={<AimOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Recall (Sensitivity)"
                value={(currentModelMetrics.recall * 100).toFixed(1)}
                suffix="%"
                prefix={<ThunderboltOutlined style={{ color: '#1890ff' }} />}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                Target: ≥95% (Critical: ≥99%)
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="False Positive Rate"
                value={(currentModelMetrics.false_positive_rate * 100).toFixed(1)}
                suffix="%"
                prefix={
                  currentModelMetrics.false_positive_rate < 0.05 ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <WarningOutlined style={{ color: '#faad14' }} />
                  )
                }
                valueStyle={{
                  color: currentModelMetrics.false_positive_rate < 0.05 ? '#52c41a' : '#faad14',
                }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                Target: ≤10%
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="MCC Score"
                value={currentModelMetrics.mcc?.toFixed(3) || 'N/A'}
                prefix={<LineChartOutlined style={{ color: '#722ed1' }} />}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                Matthews Correlation
              </Text>
            </Card>
          </Col>
        </Row>
      )}

      {/* Tabs */}
      <Tabs defaultActiveKey="training">
        {/* Training Runs */}
        <TabPane
          tab={
            <span>
              <PlayCircleOutlined />
              Training Runs
            </span>
          }
          key="training"
        >
          <Card>
            <Table
              columns={trainingColumns}
              dataSource={trainingRuns}
              rowKey="id"
              pagination={{ pageSize: 5 }}
              expandable={{
                expandedRowRender: record => (
                  <div style={{ padding: 16 }}>
                    <Row gutter={[16, 16]}>
                      <Col span={8}>
                        <Text strong>Configuration:</Text>
                        <ul style={{ marginTop: 8 }}>
                          <li>Epochs: {record.config.epochs}</li>
                          <li>Batch Size: {record.config.batch_size}</li>
                          <li>Learning Rate: {record.config.learning_rate}</li>
                          <li>Early Stopping: {record.config.early_stopping_patience} epochs</li>
                          <li>Class Weights: {record.config.class_weights_enabled ? 'Yes' : 'No'}</li>
                          <li>Focal Loss: {record.config.focal_loss_enabled ? 'Yes' : 'No'}</li>
                        </ul>
                      </Col>
                      <Col span={8}>
                        <Text strong>Metrics:</Text>
                        <ul style={{ marginTop: 8 }}>
                          <li>Precision: {(record.metrics.precision * 100).toFixed(1)}%</li>
                          <li>Recall: {(record.metrics.recall * 100).toFixed(1)}%</li>
                          <li>F1 Score: {(record.metrics.f1_score * 100).toFixed(1)}%</li>
                          <li>Loss: {record.metrics.loss.toFixed(4)}</li>
                          <li>Val Accuracy: {((record.metrics.val_accuracy || 0) * 100).toFixed(1)}%</li>
                        </ul>
                      </Col>
                      <Col span={8}>
                        {record.best_checkpoint && (
                          <>
                            <Text strong>Best Checkpoint:</Text>
                            <br />
                            <Text code>{record.best_checkpoint}</Text>
                          </>
                        )}
                      </Col>
                    </Row>
                  </div>
                ),
              }}
            />
          </Card>
        </TabPane>

        {/* Evaluations */}
        <TabPane
          tab={
            <span>
              <ExperimentOutlined />
              Evaluations
            </span>
          }
          key="evaluations"
        >
          <Card>
            {evaluations.length === 0 ? (
              <Empty description="No evaluations yet" />
            ) : (
              evaluations.map(evalResult => (
                <Card key={evalResult.id} style={{ marginBottom: 16 }} type="inner" title={`Model ${evalResult.model_version}`}>
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Title level={5}>Overall Metrics</Title>
                      <Row gutter={[8, 8]}>
                        <Col span={12}>
                          <Statistic title="Accuracy" value={(evalResult.metrics.accuracy * 100).toFixed(1)} suffix="%" />
                        </Col>
                        <Col span={12}>
                          <Statistic title="F1 Score" value={(evalResult.metrics.f1_score * 100).toFixed(1)} suffix="%" />
                        </Col>
                        <Col span={12}>
                          <Statistic title="ROC AUC" value={evalResult.roc_auc?.toFixed(3)} />
                        </Col>
                        <Col span={12}>
                          <Statistic title="PR AUC" value={evalResult.pr_auc?.toFixed(3)} />
                        </Col>
                      </Row>
                    </Col>
                    <Col span={12}>
                      <Title level={5}>Class-wise Performance</Title>
                      {evalResult.metrics.class_metrics && (
                        <Table
                          size="small"
                          pagination={false}
                          dataSource={Object.entries(evalResult.metrics.class_metrics).map(([cls, metrics]) => ({
                            class: cls,
                            ...metrics,
                          }))}
                          columns={[
                            { title: 'Class', dataIndex: 'class', key: 'class' },
                            {
                              title: 'Precision',
                              dataIndex: 'precision',
                              key: 'precision',
                              render: (v: number) => `${(v * 100).toFixed(1)}%`,
                            },
                            {
                              title: 'Recall',
                              dataIndex: 'recall',
                              key: 'recall',
                              render: (v: number) => `${(v * 100).toFixed(1)}%`,
                            },
                            {
                              title: 'F1',
                              dataIndex: 'f1_score',
                              key: 'f1_score',
                              render: (v: number) => `${(v * 100).toFixed(1)}%`,
                            },
                          ]}
                          rowKey="class"
                        />
                      )}
                    </Col>
                  </Row>
                </Card>
              ))
            )}
          </Card>
        </TabPane>

        {/* Continuous Learning */}
        <TabPane
          tab={
            <span>
              <HistoryOutlined />
              Feedback & Learning
            </span>
          }
          key="feedback"
        >
          <Row gutter={[16, 16]}>
            <Col span={16}>
              <Card title="Recent Feedback">
                <Table
                  dataSource={feedback}
                  rowKey="id"
                  pagination={{ pageSize: 5 }}
                  columns={[
                    {
                      title: 'Type',
                      dataIndex: 'feedback_type',
                      key: 'feedback_type',
                      render: (type: string) => {
                        const colors: Record<string, string> = {
                          false_positive: 'orange',
                          false_negative: 'red',
                          correct: 'green',
                          severity_change: 'blue',
                        };
                        return <Tag color={colors[type]}>{type.replace('_', ' ').toUpperCase()}</Tag>;
                      },
                    },
                    {
                      title: 'Original Prediction',
                      dataIndex: 'original_prediction',
                      key: 'original_prediction',
                    },
                    {
                      title: 'Notes',
                      dataIndex: 'notes',
                      key: 'notes',
                      ellipsis: true,
                    },
                    {
                      title: 'Used in Retraining',
                      dataIndex: 'used_in_retraining',
                      key: 'used_in_retraining',
                      render: (used: boolean) =>
                        used ? (
                          <Tag color="green">Yes</Tag>
                        ) : (
                          <Tag color="default">Pending</Tag>
                        ),
                    },
                    {
                      title: 'Submitted',
                      dataIndex: 'submitted_at',
                      key: 'submitted_at',
                      render: (date: string) => new Date(date).toLocaleDateString(),
                    },
                  ]}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Retraining Recommendation">
                <Alert
                  message="Retraining Suggested"
                  description={
                    <div>
                      <Paragraph>
                        <Text strong>Pending Feedback:</Text> {feedback.filter(f => !f.used_in_retraining).length}
                      </Paragraph>
                      <Paragraph>
                        <Text strong>Reason:</Text> New false positive patterns detected
                      </Paragraph>
                      <Button type="primary" icon={<PlayCircleOutlined />} block style={{ marginTop: 8 }}>
                        Start Retraining
                      </Button>
                    </div>
                  }
                  type="warning"
                  showIcon
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Training Configuration Modal */}
      <Modal
        title="Start New Training"
        open={trainingModalVisible}
        onCancel={() => setTrainingModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleStartTraining}
          initialValues={{
            epochs: 50,
            batch_size: 32,
            learning_rate: 0.001,
            early_stopping_patience: 5,
            class_weights_enabled: true,
            focal_loss_enabled: true,
            validation_split: 0.2,
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="epochs" label="Epochs">
                <InputNumber min={10} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="batch_size" label="Batch Size">
                <InputNumber min={8} max={128} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="learning_rate" label="Learning Rate">
                <InputNumber min={0.0001} max={0.01} step={0.0001} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="early_stopping_patience" label="Early Stopping Patience">
                <InputNumber min={3} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="validation_split" label="Validation Split">
            <Slider min={0.1} max={0.3} step={0.05} marks={{ 0.1: '10%', 0.2: '20%', 0.3: '30%' }} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="class_weights_enabled" label="Class Weights" valuePropName="checked">
                <Switch checkedChildren="Enabled" unCheckedChildren="Disabled" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="focal_loss_enabled" label="Focal Loss" valuePropName="checked">
                <Switch checkedChildren="Enabled" unCheckedChildren="Disabled" />
              </Form.Item>
            </Col>
          </Row>

          <Alert
            message="Training will use the current dataset with the latest feedback incorporated."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setTrainingModalVisible(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />}>
                Start Training
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
