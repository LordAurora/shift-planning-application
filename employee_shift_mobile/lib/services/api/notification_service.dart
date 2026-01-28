import '../../core/config/api_endpoints.dart';
import '../../data/models/notification_model.dart';
import 'api_client.dart';

/// Bildirim servisi
class NotificationService {
  final ApiClient _client;
  
  NotificationService({required ApiClient client}) : _client = client;
  
  /// Tüm bildirimleri getir
  Future<List<AppNotification>> getNotifications({bool? isRead}) async {
    final queryParams = <String, dynamic>{};
    if (isRead != null) {
      queryParams['is_read'] = isRead;
    }
    
    final response = await _client.get(
      ApiEndpoints.notifications,
      queryParameters: queryParams.isNotEmpty ? queryParams : null,
    );
    
    final items = response.data as List<dynamic>;
    return items
        .map((item) => AppNotification.fromJson(item as Map<String, dynamic>))
        .toList();
  }
  
  /// Okunmamış bildirimleri getir
  Future<List<AppNotification>> getUnreadNotifications() async {
    return getNotifications(isRead: false);
  }
  
  /// Bildirimi okundu olarak işaretle
  Future<void> markAsRead(int notificationId) async {
    await _client.put(ApiEndpoints.markAsRead(notificationId));
  }
  
  /// Tüm bildirimleri okundu olarak işaretle
  Future<void> markAllAsRead() async {
    await _client.put(ApiEndpoints.markAllAsRead);
  }
  
  /// Bildirimi sil
  Future<void> deleteNotification(int notificationId) async {
    await _client.delete(ApiEndpoints.notificationById(notificationId));
  }
  
  /// Okunmamış bildirim sayısını al
  Future<int> getUnreadCount() async {
    final notifications = await getUnreadNotifications();
    return notifications.length;
  }
}
