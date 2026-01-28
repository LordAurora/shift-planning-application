import 'dart:async';
import 'package:flutter/foundation.dart';
import '../core/config/app_config.dart';
import '../data/models/notification_model.dart';
import '../services/api/notification_service.dart';
import '../services/connectivity_service.dart';

/// Bildirim provider'ı - Otomatik senkronizasyon
class NotificationProvider extends ChangeNotifier {
  final NotificationService _notificationService;
  final ConnectivityService _connectivityService;
  
  // Veri
  List<AppNotification> _notifications = [];
  int _unreadCount = 0;
  
  // Durum
  bool _isLoading = false;
  String? _errorMessage;
  
  // Zamanlayıcılar
  Timer? _autoSyncTimer;
  StreamSubscription? _connectivitySubscription;
  
  // Deep link için bildirim
  AppNotification? _pendingNotification;
  
  NotificationProvider({
    required NotificationService notificationService,
    required ConnectivityService connectivityService,
  })  : _notificationService = notificationService,
        _connectivityService = connectivityService {
    _setupConnectivityListener();
  }
  
  // Getters
  List<AppNotification> get notifications => _notifications;
  List<AppNotification> get unreadNotifications => 
      _notifications.where((n) => !n.isRead).toList();
  int get unreadCount => _unreadCount;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get hasUnread => _unreadCount > 0;
  AppNotification? get pendingNotification => _pendingNotification;
  
  /// Bağlantı değişikliği dinleyicisi
  void _setupConnectivityListener() {
    _connectivitySubscription = _connectivityService.connectionStatusStream.listen(
      (status) {
        if (status == ConnectionStatus.online) {
          refreshNotifications();
        }
      },
    );
  }
  
  /// Otomatik senkronizasyonu başlat
  void startAutoSync() {
    stopAutoSync();
    
    _autoSyncTimer = Timer.periodic(
      Duration(seconds: AppConfig.notificationSyncInterval),
      (_) => _autoRefresh(),
    );
    
    if (kDebugMode) {
      print('⏱️ Bildirim otomatik senkronizasyonu başlatıldı (${AppConfig.notificationSyncInterval}s)');
    }
  }
  
  /// Otomatik senkronizasyonu durdur
  void stopAutoSync() {
    _autoSyncTimer?.cancel();
    _autoSyncTimer = null;
  }
  
  /// Otomatik yenileme
  Future<void> _autoRefresh() async {
    if (!_connectivityService.isOnline) return;
    
    try {
      final previousCount = _unreadCount;
      await _fetchUnreadCount();
      
      // Yeni bildirim varsa
      if (_unreadCount > previousCount) {
        await fetchNotifications();
        // Yeni bildirimler için callback tetiklenebilir
      }
    } catch (e) {
      if (kDebugMode) {
        print('⚠️ Otomatik bildirim yenileme hatası: $e');
      }
    }
  }
  
  /// Bildirimleri yükle
  Future<void> fetchNotifications() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      _notifications = await _notificationService.getNotifications();
      _unreadCount = _notifications.where((n) => !n.isRead).length;
    } catch (e) {
      _errorMessage = 'Bildirimler yüklenemedi';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  /// Bildirimleri yenile
  Future<void> refreshNotifications() async {
    try {
      _notifications = await _notificationService.getNotifications();
      _unreadCount = _notifications.where((n) => !n.isRead).length;
      _errorMessage = null;
      notifyListeners();
    } catch (e) {
      // Yenileme hatası sessizce geç
    }
  }
  
  /// Okunmamış sayısını güncelle
  Future<void> _fetchUnreadCount() async {
    _unreadCount = await _notificationService.getUnreadCount();
    notifyListeners();
  }
  
  /// Bildirimi okundu olarak işaretle
  Future<void> markAsRead(int notificationId) async {
    try {
      await _notificationService.markAsRead(notificationId);
      
      // Yerel listeyi güncelle
      final index = _notifications.indexWhere((n) => n.id == notificationId);
      if (index != -1) {
        _notifications[index] = _notifications[index].copyWith(isRead: true);
        _unreadCount = _notifications.where((n) => !n.isRead).length;
        notifyListeners();
      }
    } catch (e) {
      // Hata durumunda yeniden yükle
      await refreshNotifications();
    }
  }
  
  /// Tüm bildirimleri okundu işaretle
  Future<void> markAllAsRead() async {
    try {
      await _notificationService.markAllAsRead();
      
      // Yerel listeyi güncelle
      _notifications = _notifications.map((n) => n.copyWith(isRead: true)).toList();
      _unreadCount = 0;
      notifyListeners();
    } catch (e) {
      await refreshNotifications();
    }
  }
  
  /// Bildirimi sil
  Future<void> deleteNotification(int notificationId) async {
    try {
      await _notificationService.deleteNotification(notificationId);
      
      // Yerel listeden kaldır
      _notifications.removeWhere((n) => n.id == notificationId);
      _unreadCount = _notifications.where((n) => !n.isRead).length;
      notifyListeners();
    } catch (e) {
      await refreshNotifications();
    }
  }
  
  /// Pending bildirimi ayarla (deep link için)
  void setPendingNotification(AppNotification notification) {
    _pendingNotification = notification;
    notifyListeners();
  }
  
  /// Pending bildirimi temizle
  void clearPendingNotification() {
    _pendingNotification = null;
    notifyListeners();
  }
  
  @override
  void dispose() {
    stopAutoSync();
    _connectivitySubscription?.cancel();
    super.dispose();
  }
}
