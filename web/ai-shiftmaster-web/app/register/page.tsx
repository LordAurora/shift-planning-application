'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Alert, Button, Checkbox, Form, Input, Typography, message } from 'antd';
import { CheckCircleFilled, LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../lib/services';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

interface RegisterForm {
  name: string;
  email: string;
  password: string;
  confirm: string;
  terms: boolean;
}

const highlights = [
  'AI-generated schedules in seconds',
  'Labor rules and rest periods enforced automatically',
  'Employee preferences built into every plan',
  'Mobile app for shifts, leave and notifications',
];

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFinish = async (values: RegisterForm) => {
    setLoading(true);
    setError(null);
    try {
      await authService.register({ name: values.name, email: values.email, password: values.password });
      message.success('Account created. Signing you in…');
      const ok = await login(values.email, values.password);
      router.push(ok ? '/dashboard' : '/login');
    } catch (err) {
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : null;
      setError(typeof detail === 'string' ? detail : 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <Link href="/landing" className="auth-logo">ShiftMaster AI</Link>
        <div>
          <h2>Plan every shift with confidence.</h2>
          <ul>
            {highlights.map((h) => (
              <li key={h}><CheckCircleFilled /> {h}</li>
            ))}
          </ul>
        </div>
        <p className="auth-foot">Your workspace is ready the moment you sign up.</p>
      </aside>

      <main className="auth-panel">
        <div className="auth-card">
          <Title level={2} style={{ marginBottom: 4 }}>Create your account</Title>
          <Text type="secondary">Start planning shifts in minutes.</Text>

          {error && <Alert type="error" showIcon title={error} style={{ marginTop: 24 }} />}

          <Form<RegisterForm> layout="vertical" size="large" requiredMark={false} onFinish={onFinish} style={{ marginTop: 24 }}>
            <Form.Item name="name" label="Full name" rules={[{ required: true, min: 2, message: 'Enter your name' }]}>
              <Input prefix={<UserOutlined />} placeholder="Jane Cooper" autoComplete="name" />
            </Form.Item>
            <Form.Item name="email" label="Work email" rules={[{ required: true, type: 'email', message: 'Enter a valid email address' }]}>
              <Input prefix={<MailOutlined />} placeholder="jane@company.com" autoComplete="email" />
            </Form.Item>
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, min: 8, message: 'Use at least 8 characters' }]}
              hasFeedback
            >
              <Input.Password prefix={<LockOutlined />} placeholder="At least 8 characters" autoComplete="new-password" />
            </Form.Item>
            <Form.Item
              name="confirm"
              label="Confirm password"
              dependencies={['password']}
              hasFeedback
              rules={[
                { required: true, message: 'Confirm your password' },
                ({ getFieldValue }) => ({
                  validator: (_, value) =>
                    !value || getFieldValue('password') === value ? Promise.resolve() : Promise.reject(new Error('Passwords do not match')),
                }),
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Repeat password" autoComplete="new-password" />
            </Form.Item>
            <Form.Item
              name="terms"
              valuePropName="checked"
              rules={[{ validator: (_, v) => (v ? Promise.resolve() : Promise.reject(new Error('Please accept the terms'))) }]}
            >
              <Checkbox>I agree to the Terms of Service and Privacy Policy</Checkbox>
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>Create account</Button>
          </Form>

          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Text type="secondary">Already have an account? </Text>
            <Link href="/login">Sign in</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
