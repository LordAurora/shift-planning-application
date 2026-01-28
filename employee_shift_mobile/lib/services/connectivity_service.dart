import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

/// Bağlantı durumu enum'u
enum ConnectionStatus {
  online,
  offline,
}

/// Bağlantı yönetim servisi - Otomatik bağlantı kontrolü
class ConnectivityService {
  final Connectivity _connectivity = Connectivity();
  
  // Bağlantı durumu stream'i
  final _connectionStatusController = StreamController<ConnectionStatus>.broadcast();
  Stream<ConnectionStatus> get connectionStatusStream => _connectionStatusController.stream;
  
  // Mevcut durum
  ConnectionStatus _currentStatus = ConnectionStatus.online;
  ConnectionStatus get currentStatus => _currentStatus;
  
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  
  /// Servisi başlat
  Future<void> init() async {
    // İlk durumu kontrol et
    await checkConnection();
    
    // Değişiklikleri dinle
    _subscription = _connectivity.onConnectivityChanged.listen(_handleConnectionChange);
  }
  
  /// Bağlantı değişikliği işleyici
  void _handleConnectionChange(List<ConnectivityResult> results) {
    final hasConnection = results.any((result) => 
      result != ConnectivityResult.none
    );
    
    final newStatus = hasConnection ? ConnectionStatus.online : ConnectionStatus.offline;
    
    if (newStatus != _currentStatus) {
      _currentStatus = newStatus;
      _connectionStatusController.add(newStatus);
      
      if (kDebugMode) {
        print('🌐 Bağlantı durumu değişti: ${newStatus.name}');
      }
    }
  }
  
  /// Manuel bağlantı kontrolü
  Future<bool> checkConnection() async {
    try {
      final results = await _connectivity.checkConnectivity();
      final hasConnection = results.any((result) => 
        result != ConnectivityResult.none
      );
      
      _currentStatus = hasConnection ? ConnectionStatus.online : ConnectionStatus.offline;
      _connectionStatusController.add(_currentStatus);
      
      return hasConnection;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Bağlantı kontrolü hatası: $e');
      }
      return false;
    }
  }
  
  /// Çevrimiçi mi?
  bool get isOnline => _currentStatus == ConnectionStatus.online;
  
  /// Çevrimdışı mı?
  bool get isOffline => _currentStatus == ConnectionStatus.offline;
  
  /// Servisi temizle
  void dispose() {
    _subscription?.cancel();
    _connectionStatusController.close();
  }
}
