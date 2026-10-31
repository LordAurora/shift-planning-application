import 'dart:async';
import 'package:flutter/foundation.dart';
import '../core/config/app_config.dart';
import '../data/models/shift_model.dart';
import '../services/api/shift_service.dart';
import '../services/connectivity_service.dart';

/// Vardiya provider'ı - Otomatik senkronizasyon
class ShiftProvider extends ChangeNotifier {
  final ShiftService _shiftService;
  final ConnectivityService _connectivityService;
  
  // Veri
  List<Shift> _todayShifts = [];
  List<Shift> _weeklyShifts = [];
  List<Shift> _upcomingShifts = [];
  Shift? _currentShift;
  
  // Durum
  bool _isLoading = false;
  bool _isRefreshing = false;
  String? _errorMessage;
  DateTime? _lastSyncTime;
  
  // Zamanlayıcılar
  Timer? _autoSyncTimer;
  StreamSubscription? _connectivitySubscription;
  
  // Hafta başlangıcı
  DateTime _selectedWeekStart = _getWeekStart(DateTime.now());
  
  ShiftProvider({
    required ShiftService shiftService,
    required ConnectivityService connectivityService,
  })  : _shiftService = shiftService,
        _connectivityService = connectivityService {
    _setupConnectivityListener();
  }
  
  // Getters
  List<Shift> get todayShifts => _todayShifts;
  List<Shift> get weeklyShifts => _weeklyShifts;
  List<Shift> get upcomingShifts => _upcomingShifts;
  Shift? get currentShift => _currentShift;
  bool get isLoading => _isLoading;
  bool get isRefreshing => _isRefreshing;
  String? get errorMessage => _errorMessage;
  DateTime? get lastSyncTime => _lastSyncTime;
  DateTime get selectedWeekStart => _selectedWeekStart;
  
  /// Mevcut aktif vardiya
  Shift? get activeShift {
    return _todayShifts.cast<Shift?>().firstWhere(
      (s) => s!.isActive,
      orElse: () => null,
    );
  }
  
  /// Bağlantı değişikliği dinleyicisi
  void _setupConnectivityListener() {
    _connectivitySubscription = _connectivityService.connectionStatusStream.listen(
      (status) {
        if (status == ConnectionStatus.online) {
          // Bağlantı geri geldi - otomatik senkronizasyon
          if (kDebugMode) {
            print('🔄 Bağlantı geri geldi, vardiyalar senkronize ediliyor...');
          }
          refreshAll();
        }
      },
    );
  }
  
  /// Otomatik senkronizasyonu başlat
  void startAutoSync() {
    stopAutoSync();
    
    // Belirli aralıklarla otomatik senkronizasyon
    _autoSyncTimer = Timer.periodic(
      Duration(seconds: AppConfig.shiftSyncInterval),
      (_) => _autoRefresh(),
    );
    
    if (kDebugMode) {
      print('⏱️ Vardiya otomatik senkronizasyonu başlatıldı (${AppConfig.shiftSyncInterval}s)');
    }
  }
  
  /// Otomatik senkronizasyonu durdur
  void stopAutoSync() {
    _autoSyncTimer?.cancel();
    _autoSyncTimer = null;
  }
  
  /// Otomatik yenileme (arka plan)
  Future<void> _autoRefresh() async {
    if (!_connectivityService.isOnline) return;
    
    try {
      await _fetchTodayShifts();
      _lastSyncTime = DateTime.now();
      notifyListeners();
    } catch (e) {
      // Otomatik yenilemede hata sessizce geç
      if (kDebugMode) {
        print('⚠️ Otomatik vardiya yenileme hatası: $e');
      }
    }
  }
  
  /// Tüm verileri yenile
  Future<void> refreshAll() async {
    if (_isRefreshing) return;
    
    _isRefreshing = true;
    notifyListeners();
    
    try {
      await Future.wait([
        _fetchTodayShifts(),
        _fetchWeeklyShifts(),
        _fetchUpcomingShifts(),
      ]);
      
      _lastSyncTime = DateTime.now();
      _errorMessage = null;
    } catch (e) {
      _errorMessage = 'Could not load shifts';
    } finally {
      _isRefreshing = false;
      notifyListeners();
    }
  }
  
  /// İlk veri yüklemesi
  Future<void> loadInitialData({int? employeeId}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      await Future.wait([
        _fetchTodayShifts(employeeId: employeeId),
        _fetchWeeklyShifts(employeeId: employeeId),
        _fetchUpcomingShifts(employeeId: employeeId),
      ]);
      
      _lastSyncTime = DateTime.now();
    } catch (e) {
      _errorMessage = 'Could not load shifts';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  /// Bugünkü vardiyaları getir
  Future<void> _fetchTodayShifts({int? employeeId}) async {
    _todayShifts = await _shiftService.getTodayShifts(employeeId: employeeId);
    _updateCurrentShift();
  }
  
  /// Haftalık vardiyaları getir
  Future<void> _fetchWeeklyShifts({int? employeeId}) async {
    _weeklyShifts = await _shiftService.getWeeklyShifts(
      weekStart: _selectedWeekStart,
      employeeId: employeeId,
    );
  }
  
  /// Yaklaşan vardiyaları getir
  Future<void> _fetchUpcomingShifts({int? employeeId}) async {
    _upcomingShifts = await _shiftService.getUpcomingShifts(
      employeeId: employeeId,
      limit: 5,
    );
  }
  
  /// Aktif vardiyayı güncelle
  void _updateCurrentShift() {
    _currentShift = activeShift;
  }
  
  /// Hafta seç
  Future<void> selectWeek(DateTime weekStart) async {
    _selectedWeekStart = _getWeekStart(weekStart);
    await _fetchWeeklyShifts();
    notifyListeners();
  }
  
  /// Önceki hafta
  Future<void> previousWeek() async {
    await selectWeek(_selectedWeekStart.subtract(const Duration(days: 7)));
  }
  
  /// Sonraki hafta
  Future<void> nextWeek() async {
    await selectWeek(_selectedWeekStart.add(const Duration(days: 7)));
  }
  
  /// Bu hafta
  Future<void> currentWeek() async {
    await selectWeek(DateTime.now());
  }
  
  /// Belirli bir gündeki vardiyalar
  List<Shift> getShiftsForDay(DateTime day) {
    return _weeklyShifts.where((shift) {
      return shift.startTime.year == day.year &&
          shift.startTime.month == day.month &&
          shift.startTime.day == day.day;
    }).toList();
  }
  
  /// Hafta başlangıcını hesapla (Pazartesi)
  static DateTime _getWeekStart(DateTime date) {
    final weekday = date.weekday;
    return DateTime(date.year, date.month, date.day)
        .subtract(Duration(days: weekday - 1));
  }
  
  @override
  void dispose() {
    stopAutoSync();
    _connectivitySubscription?.cancel();
    super.dispose();
  }
}
