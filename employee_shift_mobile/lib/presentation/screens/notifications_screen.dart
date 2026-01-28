import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_strings.dart';
import '../../providers/notification_provider.dart';
import '../widgets/widgets.dart';

/// Bildirimler Ekranı
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    await context.read<NotificationProvider>().fetchNotifications();
  }

  Future<void> _refresh() async {
    await context.read<NotificationProvider>().refreshNotifications();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(AppStrings.notifications),
        actions: [
          Consumer<NotificationProvider>(
            builder: (context, provider, _) {
              if (!provider.hasUnread) return const SizedBox.shrink();
              return TextButton(
                onPressed: () => provider.markAllAsRead(),
                child: const Text(AppStrings.markAllRead),
              );
            },
          ),
        ],
      ),
      body: Consumer<NotificationProvider>(
        builder: (context, notificationProvider, _) {
          if (notificationProvider.isLoading) {
            return const LoadingWidget(message: 'Bildirimler yükleniyor...');
          }

          if (notificationProvider.notifications.isEmpty) {
            return const EmptyStateWidget(
              title: AppStrings.noNotifications,
              subtitle: 'Henüz bildiriminiz bulunmuyor',
              icon: Icons.notifications_off_outlined,
            );
          }

          return RefreshIndicator(
            onRefresh: _refresh,
            color: AppColors.primary,
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: notificationProvider.notifications.length,
              itemBuilder: (context, index) {
                final notification = notificationProvider.notifications[index];
                return NotificationCard(
                  notification: notification,
                  onTap: () {
                    // Bildirimi okundu işaretle
                    if (!notification.isRead) {
                      notificationProvider.markAsRead(notification.id);
                    }
                    
                    // Deep link yönlendirmesi
                    if (notification.targetRoute != null) {
                      Navigator.of(context).pushNamed(notification.targetRoute!);
                    }
                  },
                  onDismiss: () {
                    notificationProvider.deleteNotification(notification.id);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Bildirim silindi'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}
