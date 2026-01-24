'use client';

import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [form] = Form.useForm();
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (values: { email: string; password: string }) => {
    const success = await login(values.email, values.password);
    if (success) {
      router.push('/dashboard');
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f5f5f5',
        padding: 24,
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 420,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        }}
        bordered={false}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8, color: '#1e3a5f' }}>
            ShiftMaster AI
          </Title>
          <Text type="secondary">AI-Powered Shift Planning System</Text>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            closable
            onClose={clearError}
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          size="large"
          requiredMark={false}
        >
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter your email' },
              { type: 'email', message: 'Please enter a valid email' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="Enter your email" autoComplete="email" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: 'Please enter your password' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              block
              style={{ height: 44 }}
            >
              Sign In
            </Button>
          </Form.Item>
        </Form>

        <div
          style={{
            textAlign: 'center',
            padding: '16px 0',
            borderTop: '1px solid #f0f0f0',
            marginTop: 16,
          }}
        >
          <Text type="secondary" style={{ fontSize: 13 }}>
            Henüz hesabınız yok mu?{' '}
            <a
              onClick={() => router.push('/register')}
              style={{ color: '#1e3a5f', fontWeight: 500, cursor: 'pointer' }}
            >
              Şirketinizi Kayıt Edin
            </a>
          </Text>
          <br />
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            Demo Credentials:
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            admin@example.com / admin123
          </Text>
        </div>
      </Card>
    </div>
  );
}
