import 'dart:async';
import 'package:flutter/foundation.dart';
import '../core/config/app_config.dart';
import '../data/models/leave_request_model.dart';
import '../services/api/leave_request_service.dart';
import '../services/connectivity_service.dart';

/// İzin talebi provider'ı - Otomatik durum güncelleme
class LeaveRequestProvider extends ChangeNotifier {
  final LeaveRequestService _leaveService;
  final ConnectivityService _connectivityService;
  
  // Veri
  List<LeaveRequest> _myRequests = [];
  
  // Durum
  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _errorMessage;
  
  // Zamanlayıcılar
  Timer? _autoSyncTimer;
  StreamSubscription? _connectivitySubscription;
  
  LeaveRequestProvider({
    required LeaveRequestService leaveService,
    required ConnectivityService connectivityService,
  })  : _leaveService = leaveService,
        _connectivityService = connectivityService {
    _setupConnectivityListener();
  }
  
  // Getters
  List<LeaveRequest> get myRequests => _myRequests;
  List<LeaveRequest> get pendingRequests => 
      _myRequests.where((r) => r.isPending).toList();
  List<LeaveRequest> get approvedRequests => 
      _myRequests.where((r) => r.isApproved).toList();
  List<LeaveRequest> get rejectedRequests => 
      _myRequests.where((r) => r.isRejected).toList();
  bool get isLoading => _isLoading;
  bool get isSubmitting => _isSubmitting;
  String? get errorMessage => _errorMessage;
  bool get hasPendingRequests => pendingRequests.isNotEmpty;
  
  /// Bağlantı değişikliği dinleyicisi
  void _setupConnectivityListener() {
    _connectivitySubscription = _connectivityService.connectionStatusStream.listen(
      (status) {
        if (status == ConnectionStatus.online) {
          refreshRequests();
        }
      },
    );
  }
  
  /// Otomatik senkronizasyonu başlat
  void startAutoSync() {
    stopAutoSync();
    
    _autoSyncTimer = Timer.periodic(
      Duration(seconds: AppConfig.leaveStatusSyncInterval),
      (_) => _autoRefresh(),
    );
    
    if (kDebugMode) {
      print('⏱️ İzin talebi otomatik senkronizasyonu başlatıldı');
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
      final previousPending = pendingRequests.map((r) => r.id).toList();
      await _fetchMyRequests();
      
      // Durum değişikliği kontrolü
      for (final request in _myRequests) {
        if (previousPending.contains(request.id) && !request.isPending) {
          // Durum değişti - bildirim gösterilebilir
          if (kDebugMode) {
            print('📋 İzin talebi durumu değişti: ${request.id} -> ${request.status.displayName}');
          }
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('⚠️ Otomatik izin talebi yenileme hatası: $e');
      }
    }
  }
  
  /// İzin taleplerini yükle
  Future<void> fetchMyRequests() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      await _fetchMyRequests();
    } catch (e) {
      _errorMessage = 'Could not load leave requests';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  /// İzin taleplerini getir
  Future<void> _fetchMyRequests() async {
    _myRequests = await _leaveService.getMyLeaveRequests();
    notifyListeners();
  }
  
  /// İzin taleplerini yenile
  Future<void> refreshRequests() async {
    try {
      await _fetchMyRequests();
      _errorMessage = null;
    } catch (e) {
      // Yenileme hatası sessizce geç
    }
  }
  
  /// Yeni izin talebi oluştur
  Future<bool> createRequest(CreateLeaveRequest request) async {
    _isSubmitting = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final newRequest = await _leaveService.createLeaveRequest(request);
      _myRequests.insert(0, newRequest);
      
      _isSubmitting = false;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = 'Could not create the leave request';
      _isSubmitting = false;
      notifyListeners();
      return false;
    }
  }
  
  /// İzin talebini iptal et
  Future<bool> cancelRequest(int requestId) async {
    try {
      await _leaveService.cancelLeaveRequest(requestId);
      _myRequests.removeWhere((r) => r.id == requestId);
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = 'Could not cancel the leave request';
      notifyListeners();
      return false;
    }
  }
  
  /// Belirli bir izin talebini getir
  LeaveRequest? getRequestById(int id) {
    return _myRequests.cast<LeaveRequest?>().firstWhere(
      (r) => r!.id == id,
      orElse: () => null,
    );
  }
  
  @override
  void dispose() {
    stopAutoSync();
    _connectivitySubscription?.cancel();
    super.dispose();
  }
}
