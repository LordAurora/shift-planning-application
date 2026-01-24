'use client';

import React from 'react';
import { Drawer, List, Typography, Button, Tag, Empty, Spin } from 'antd';
import { CheckOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNotificationStore } from '../store/notificationStore';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Text, Title } = Typography;

interface NotificationPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const { notifications, isLoading, markAsRead, markAllAsRead } = useNotificationStore();

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'red';
      case 'warning':
        return 'orange';
      case 'success':
        return 'green';
      default:
        return 'blue';
    }
  };

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={5} style={{ margin: 0 }}>
            Notifications
          </Title>
          {notifications.length > 0 && (
            <Button type="link" size="small" onClick={markAllAsRead}>
              Mark all as read
            </Button>
          )}
        </div>
      }
      placement="right"
      onClose={onClose}
      open={open}
      width={400}
    >
      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin />
        </div>
      ) : notifications.length === 0 ? (
        <Empty description="No notifications" />
      ) : (
        <List
          dataSource={notifications}
          renderItem={(notification) => (
            <List.Item
              style={{
                background: notification.is_read ? 'transparent' : '#f6f8fa',
                padding: '12px 16px',
                marginBottom: 8,
                borderRadius: 4,
                border: '1px solid #f0f0f0',
              }}
              actions={[
                !notification.is_read && (
                  <Button
                    key="read"
                    type="text"
                    size="small"
                    icon={<CheckOutlined />}
                    onClick={() => markAsRead(notification.id)}
                  />
                ),
              ].filter(Boolean)}
            >
              <List.Item.Meta
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Tag color={getTypeColor(notification.type)} style={{ margin: 0 }}>
                      {notification.type.toUpperCase()}
                    </Tag>
                    <Text strong style={{ fontSize: 14 }}>
                      {notification.title}
                    </Text>
                  </div>
                }
                description={
                  <div>
                    <Text style={{ display: 'block', marginTop: 4 }}>{notification.message}</Text>
                    <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
                      {dayjs(notification.created_at).fromNow()}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Drawer>
  );
}
