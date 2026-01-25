'use client';

import React from 'react';
import { Card, Typography, Form, Input, Button, Select, Switch, Divider, Row, Col, message } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import DashboardLayout from '../components/DashboardLayout';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;
const { Option } = Select;

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [form] = Form.useForm();

  const handleSave = (values: Record<string, unknown>) => {
    console.log('Settings:', values);
    message.success('Settings saved successfully');
  };

  return (
    <DashboardLayout>
      <div>
        <Title level={4} style={{ marginBottom: 24 }}>
          Settings
        </Title>

        <Row gutter={24}>
          <Col xs={24} lg={16}>
            <Card bordered={false} style={{ marginBottom: 24 }}>
              <Title level={5}>General Settings</Title>
              <Divider />
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSave}
                initialValues={{
                  timezone: 'UTC',
                  dateFormat: 'YYYY-MM-DD',
                  timeFormat: '24h',
                  language: 'en',
                  emailNotifications: true,
                  shiftReminders: true,
                  conflictAlerts: true,
                }}
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="timezone" label="Timezone">
                      <Select>
                        <Option value="UTC">UTC</Option>
                        <Option value="America/New_York">Eastern Time (ET)</Option>
                        <Option value="America/Chicago">Central Time (CT)</Option>
                        <Option value="America/Denver">Mountain Time (MT)</Option>
                        <Option value="America/Los_Angeles">Pacific Time (PT)</Option>
                        <Option value="Europe/London">London (GMT)</Option>
                        <Option value="Europe/Berlin">Berlin (CET)</Option>
                        <Option value="Asia/Tokyo">Tokyo (JST)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="language" label="Language">
                      <Select>
                        <Option value="en">English</Option>
                        <Option value="es">Spanish</Option>
                        <Option value="fr">French</Option>
                        <Option value="de">German</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="dateFormat" label="Date Format">
                      <Select>
                        <Option value="YYYY-MM-DD">2026-01-24</Option>
                        <Option value="DD/MM/YYYY">24/01/2026</Option>
                        <Option value="MM/DD/YYYY">01/24/2026</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="timeFormat" label="Time Format">
                      <Select>
                        <Option value="24h">24-hour (14:00)</Option>
                        <Option value="12h">12-hour (2:00 PM)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />
                <Title level={5}>Notifications</Title>

                <Form.Item
                  name="emailNotifications"
                  label="Email Notifications"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>

                <Form.Item
                  name="shiftReminders"
                  label="Shift Reminders"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>

                <Form.Item
                  name="conflictAlerts"
                  label="Conflict Alerts"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>

                <Form.Item style={{ marginTop: 24 }}>
                  <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                    Save Settings
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card bordered={false}>
              <Title level={5}>Account Information</Title>
              <Divider />
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">Name</Text>
                <br />
                <Text strong>{user?.name || 'N/A'}</Text>
              </div>
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">Email</Text>
                <br />
                <Text strong>{user?.email || 'N/A'}</Text>
              </div>
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">Role</Text>
                <br />
                <Text strong style={{ textTransform: 'capitalize' }}>{user?.role || 'N/A'}</Text>
              </div>
            </Card>

            <Card bordered={false} style={{ marginTop: 24 }}>
              <Title level={5}>System Information</Title>
              <Divider />
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">Version</Text>
                <br />
                <Text strong>1.0.0</Text>
              </div>
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary">API Status</Text>
                <br />
                <Text strong style={{ color: '#52c41a' }}>Connected</Text>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </DashboardLayout>
  );
}
