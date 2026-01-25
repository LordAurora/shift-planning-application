'use client';

import React from 'react';
import { Card, Typography, Form, Input, Button, Avatar, Divider, Row, Col, message } from 'antd';
import { UserOutlined, SaveOutlined } from '@ant-design/icons';
import DashboardLayout from '../components/DashboardLayout';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [form] = Form.useForm();

  const handleSave = (values: Record<string, unknown>) => {
    console.log('Profile update:', values);
    message.success('Profile updated successfully');
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return '#1e3a5f';
      case 'manager':
        return '#4a6fa5';
      default:
        return '#8c8c8c';
    }
  };

  return (
    <DashboardLayout>
      <div>
        <Title level={4} style={{ marginBottom: 24 }}>
          Profile
        </Title>

        <Row gutter={24}>
          <Col xs={24} md={8}>
            <Card bordered={false} style={{ textAlign: 'center' }}>
              <Avatar
                size={120}
                icon={<UserOutlined />}
                style={{ backgroundColor: getRoleColor(user?.role || ''), marginBottom: 16 }}
              />
              <Title level={4} style={{ marginBottom: 4 }}>{user?.name}</Title>
              <Text type="secondary">{user?.email}</Text>
              <br />
              <Text
                style={{
                  textTransform: 'capitalize',
                  color: getRoleColor(user?.role || ''),
                  fontWeight: 500,
                }}
              >
                {user?.role}
              </Text>
            </Card>
          </Col>

          <Col xs={24} md={16}>
            <Card bordered={false}>
              <Title level={5}>Edit Profile</Title>
              <Divider />
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSave}
                initialValues={{
                  name: user?.name,
                  email: user?.email,
                }}
              >
                <Form.Item
                  name="name"
                  label="Full Name"
                  rules={[{ required: true, message: 'Please enter your name' }]}
                >
                  <Input placeholder="Enter your full name" />
                </Form.Item>

                <Form.Item
                  name="email"
                  label="Email"
                  rules={[
                    { required: true, message: 'Please enter your email' },
                    { type: 'email', message: 'Please enter a valid email' },
                  ]}
                >
                  <Input placeholder="Enter your email" disabled />
                </Form.Item>

                <Divider />
                <Title level={5}>Change Password</Title>

                <Form.Item name="current_password" label="Current Password">
                  <Input.Password placeholder="Enter current password" />
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="new_password" label="New Password">
                      <Input.Password placeholder="Enter new password" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="confirm_password" label="Confirm Password">
                      <Input.Password placeholder="Confirm new password" />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item style={{ marginTop: 24 }}>
                  <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                    Save Changes
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </Col>
        </Row>
      </div>
    </DashboardLayout>
  );
}
