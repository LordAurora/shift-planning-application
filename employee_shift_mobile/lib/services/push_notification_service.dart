import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'storage_service.dart';

/// Push bildirim servisi - Huawei Push Kit entegrasyonu
class PushNotificationService {
  final StorageService _storage;
  final FlutterLocalNotificationsPlugin _localNotifications;
  
  // Bildirim tıklanma callback'i
  Function(String? route, Map<String, dynamic>? data)? onNotificationTapped;
  
  // Bildirim alındı callback'i (uygulama açıkken)
  Function(String title, String body, Map<String, dynamic>? data)? onNotificationReceived;
  
  PushNotificationService({required StorageService storage})
      : _storage = storage,
        _localNotifications = FlutterLocalNotificationsPlugin();
  
  /// Servisi başlat
  Future<void> init() async {
    await _initLocalNotifications();
    await _initHuaweiPush();
  }
  
  /// Yerel bildirimleri başlat
  Future<void> _initLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationResponse,
    );
    
    // Bildirim izni iste (Android 13+)
    await _requestPermissions();
  }
  
  /// İzinleri iste
  Future<void> _requestPermissions() async {
    final androidPlugin = _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    
    if (androidPlugin != null) {
      await androidPlugin.requestNotificationsPermission();
    }
  }
  
  /// Huawei Push Kit başlat
  Future<void> _initHuaweiPush() async {
    try {
      // Huawei Push Kit entegrasyonu
      // NOT: Gerçek uygulamada huawei_push paketini kullanın
      // Bu demo için simüle ediyoruz
      
      if (kDebugMode) {
        print('📱 Huawei Push Kit başlatıldı');
      }
      
      // Push token al ve kaydet
      // final token = await Push.getToken("");
      // await _savePushToken(token);
      
    } catch (e) {
      if (kDebugMode) {
        print('❌ Huawei Push Kit hatası: $e');
      }
    }
  }
  
  // ignore: unused_element
  Future<void> _savePushToken(String token) async {
    await _storage.savePushToken(token);
    if (kDebugMode) {
      print('📲 Push token kaydedildi: ${token.substring(0, 20)}...');
    }
  }
  
  /// Bildirim tıklama işleyici
  void _onNotificationResponse(NotificationResponse response) {
    if (kDebugMode) {
      print('🔔 Bildirim tıklandı: ${response.payload}');
    }
    
    // Payload'dan route ve data çıkar
    if (response.payload != null) {
      // Deep link mantığı
      final parts = response.payload!.split('|');
      final route = parts.isNotEmpty ? parts[0] : null;
      
      onNotificationTapped?.call(route, null);
    }
  }
  
  /// Yerel bildirim göster
  Future<void> showLocalNotification({
    required int id,
    required String title,
    required String body,
    String? payload,
    String channelId = 'default',
    String channelName = 'Genel Bildirimler',
  }) async {
    final androidDetails = AndroidNotificationDetails(
      channelId,
      channelName,
      importance: Importance.high,
      priority: Priority.high,
      icon: '@mipmap/ic_launcher',
      enableVibration: true,
      playSound: true,
    );
    
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    
    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.show(id, title, body, details, payload: payload);
  }
  
  /// Vardiya değişikliği bildirimi
  Future<void> showShiftChangeNotification({
    required String title,
    required String body,
  }) async {
    await showLocalNotification(
      id: DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title: title,
      body: body,
      payload: '/shifts/weekly',
      channelId: 'shift_changes',
      channelName: 'Vardiya Değişiklikleri',
    );
  }
  
  /// Acil çağrı bildirimi
  Future<void> showEmergencyNotification({
    required String title,
    required String body,
  }) async {
    await showLocalNotification(
      id: DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title: '🚨 $title',
      body: body,
      payload: '/home',
      channelId: 'emergency',
      channelName: 'Acil Bildirimler',
    );
  }
  
  /// İzin sonucu bildirimi
  Future<void> showLeaveResultNotification({
    required String title,
    required String body,
    required bool isApproved,
  }) async {
    await showLocalNotification(
      id: DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title: isApproved ? '✅ $title' : '❌ $title',
      body: body,
      payload: '/leave-requests',
      channelId: 'leave_requests',
      channelName: 'İzin Talepleri',
    );
  }
  
  /// Tüm bildirimleri temizle
  Future<void> clearAllNotifications() async {
    await _localNotifications.cancelAll();
  }
  
  /// Push token al
  String? getPushToken() {
    return _storage.getPushToken();
  }
}
