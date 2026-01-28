import 'package:flutter/foundation.dart';

/// Uygulama yapılandırma ayarları
class AppConfig {
  // API Ayarları
  static const String androidEmulatorUrl = 'http://10.0.2.2:8000/api/v1';
  static const String webLocalhostUrl = 'http://localhost:8000/api/v1';
  static const String productionUrl = 'https://api.shiftmaster.com/api/v1';
  
  // Timeout Ayarları (saniye)
  static const int connectionTimeout = 30;
  static const int receiveTimeout = 30;
  
  // Otomatik Yenileme Aralıkları (saniye)
  static const int shiftSyncInterval = 60; // Vardiya senkronizasyonu
  static const int notificationSyncInterval = 30; // Bildirim kontrolü
  static const int leaveStatusSyncInterval = 120; // İzin durumu kontrolü
  
  // Token Ayarları
  static const int tokenRefreshThreshold = 5; // Token süresi dolmadan kaç dakika önce yenilensin
  
  // Huawei Push Kit
  static const String huaweiAppId = 'YOUR_HUAWEI_APP_ID';
  
  // Ortam kontrolü
  static bool get isProduction => const String.fromEnvironment('ENV') == 'production';
  
  static String get apiBaseUrl {
    if (isProduction) return productionUrl;
    // Web ortamında 10.0.2.2 erişilemez, localhost kullan
    if (kIsWeb) return webLocalhostUrl;
    return androidEmulatorUrl;
  }
}
