'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Alert, Button, Form, Input, Typography } from 'antd';
import { CheckCircleFilled, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

const highlights = [
  'Schedules that respect rest periods and hour caps',
  'Preferences and days off built in',
  'Real-time updates for managers and employees',
];

export default function LoginPage() {
  const [form] = Form.useForm();
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (values: { email: string; password: string }) => {
    if (await login(values.email, values.password)) {
      router.push('/dashboard');
    }
  };

  const fillDemo = () => form.setFieldsValue({ email: 'admin@example.com', password: 'admin123' });

  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <Link href="/landing" className="auth-logo">ShiftMaster AI</Link>
        <div>
          <h2>Welcome back.</h2>
          <ul>
            {highlights.map((h) => (
              <li key={h}><CheckCircleFilled /> {h}</li>
            ))}
          </ul>
        </div>
        <p className="auth-foot">AI-assisted workforce scheduling</p>
      </aside>

      <main className="auth-panel">
        <div className="auth-card">
          <Title level={2} style={{ marginBottom: 4 }}>Sign in</Title>
          <Text type="secondary">Access your scheduling workspace.</Text>

          {error && (
            <Alert title={error} type="error" showIcon closable onClose={clearError} style={{ marginTop: 24 }} />
          )}

          <Form form={form} layout="vertical" onFinish={handleSubmit} size="large" requiredMark={false} style={{ marginTop: 24 }}>
            <Form.Item
              name="email"
              label="Email"
              rules={[
                { required: true, message: 'Please enter your email' },
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="you@company.com" autoComplete="email" />
            </Form.Item>
            <Form.Item name="password" label="Password" rules={[{ required: true, message: 'Please enter your password' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="Your password" autoComplete="current-password" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={isLoading} block>Sign in</Button>
          </Form>

          <div className="auth-demo">
            <Text type="secondary" style={{ fontSize: 13 }}>Exploring the demo?</Text>
            <Button type="link" size="small" onClick={fillDemo}>Use the admin demo account</Button>
          </div>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text type="secondary">New to ShiftMaster AI? </Text>
            <Link href="/register">Create an account</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
