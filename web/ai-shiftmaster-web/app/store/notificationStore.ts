'use client';

import { create } from 'zustand';
import { Notification } from '../types';
import { notificationService } from '../lib/services';

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  addNotification: (notification: Notification) => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  fetchNotifications: async () => {
    set({ isLoading: true });
    try {
      const notifications = await notificationService.getAll();
      const unreadCount = notifications.filter((n) => !n.is_read).length;
      set({ notifications, unreadCount, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      set({ isLoading: false });
    }
  },

  markAsRead: async (id: number) => {
    try {
      await notificationService.markAsRead(id);
      const notifications = get().notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      );
      const unreadCount = notifications.filter((n) => !n.is_read).length;
      set({ notifications, unreadCount });
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  },

  markAllAsRead: async () => {
    try {
      await notificationService.markAllAsRead();
      const notifications = get().notifications.map((n) => ({ ...n, is_read: true }));
      set({ notifications, unreadCount: 0 });
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  },

  addNotification: (notification: Notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + (notification.is_read ? 0 : 1),
    }));
  },
}));
