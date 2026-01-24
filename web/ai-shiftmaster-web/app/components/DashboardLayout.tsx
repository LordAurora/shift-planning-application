'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Layout, Menu, Avatar, Dropdown, Badge, Button, Typography } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  CalendarOutlined,
  SettingOutlined,
  BellOutlined,
  LogoutOutlined,
  UserOutlined,
  RobotOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FileTextOutlined,
  SecurityScanOutlined,
  CodeOutlined,
  ExperimentOutlined,
  CloudServerOutlined,
  BugOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useAuthStore } from '../store/authStore';
import { useNotificationStore } from '../store/notificationStore';
import NotificationPanel from './NotificationPanel';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const menuItems: MenuProps['items'] = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/employees',
    icon: <TeamOutlined />,
    label: 'Employees',
  },
  {
    key: '/shifts',
    icon: <CalendarOutlined />,
    label: 'Shifts',
  },
  {
    key: '/rules',
    icon: <FileTextOutlined />,
    label: 'Shift Rules',
  },
  {
    key: '/ai-optimization',
    icon: <RobotOutlined />,
    label: 'AI Optimization',
  },
  {
    key: 'security-ai',
    icon: <SecurityScanOutlined />,
    label: 'Security AI',
    children: [
      {
        key: '/security',
        icon: <DashboardOutlined />,
        label: 'Dashboard',
      },
      {
        key: '/security/scan',
        icon: <BugOutlined />,
        label: 'Vulnerability Scan',
      },
      {
        key: '/security/rules',
        icon: <CodeOutlined />,
        label: 'Detection Rules',
      },
      {
        key: '/security/training',
        icon: <ExperimentOutlined />,
        label: 'ML Training',
      },
      {
        key: '/security/migration',
        icon: <CloudServerOutlined />,
        label: 'Huawei Migration',
      },
    ],
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, isAuthenticated } = useAuthStore();
  const { unreadCount, fetchNotifications } = useNotificationStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
    }
  }, [isAuthenticated, fetchNotifications]);

  const handleMenuClick = ({ key }: { key: string }) => {
    router.push(key);
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => router.push('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => router.push('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
    },
  ];

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

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <Text
            style={{
              color: '#fff',
              fontSize: collapsed ? 16 : 18,
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}
          >
            {collapsed ? 'SM' : 'ShiftMaster AI'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 48, height: 48 }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Badge count={unreadCount} size="small">
              <Button
                type="text"
                icon={<BellOutlined style={{ fontSize: 18 }} />}
                onClick={() => setNotificationOpen(true)}
                style={{ width: 40, height: 40 }}
              />
            </Badge>
            <Dropdown menu={{ items: userMenuItems }} trigger={['click']} placement="bottomRight">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: 4,
                }}
              >
                <Avatar
                  size={36}
                  icon={<UserOutlined />}
                  style={{ backgroundColor: getRoleColor(user?.role || '') }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                  <Text style={{ fontWeight: 500 }}>{user?.name}</Text>
                  <Text type="secondary" style={{ fontSize: 12, textTransform: 'capitalize' }}>
                    {user?.role}
                  </Text>
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: '#fff',
            borderRadius: 8,
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          {children}
        </Content>
      </Layout>
      <NotificationPanel open={notificationOpen} onClose={() => setNotificationOpen(false)} />
    </Layout>
  );
}
