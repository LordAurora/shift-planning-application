import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import '../data/models/user_model.dart';
import '../services/api/auth_service.dart';
import '../services/storage_service.dart';
import '../services/push_notification_service.dart';

/// Kimlik doğrulama durumu
enum AuthStatus {
  initial,       // Başlangıç
  loading,       // Yükleniyor
  authenticated, // Giriş yapılmış
  unauthenticated, // Giriş yapılmamış
  error,         // Hata
}

/// Kimlik doğrulama provider'ı - Otomatik oturum yönetimi
class AuthProvider extends ChangeNotifier {
  final AuthService _authService;
  final StorageService _storage;
  final PushNotificationService _pushService;
  
  AuthStatus _status = AuthStatus.initial;
  User? _user;
  String? _errorMessage;
  Timer? _tokenCheckTimer;
  
  AuthProvider({
    required AuthService authService,
    required StorageService storage,
    required PushNotificationService pushService,
  })  : _authService = authService,
        _storage = storage,
        _pushService = pushService;
  
  // Getters
  AuthStatus get status => _status;
  User? get user => _user;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isLoading => _status == AuthStatus.loading;
  
  /// Uygulama başlangıcında oturum kontrolü
  Future<void> checkAuthStatus() async {
    _status = AuthStatus.loading;
    notifyListeners();
    
    try {
      // Token kontrolü
      final hasToken = await _storage.hasAccessToken();
      if (!hasToken) {
        _status = AuthStatus.unauthenticated;
        notifyListeners();
        return;
      }
      
      // Token geçerliliğini kontrol et
      final token = await _storage.getAccessToken();
      if (token != null && JwtDecoder.isExpired(token)) {
        // Token süresi dolmuş - yenilemeyi dene
        try {
          final response = await _authService.refreshToken();
          await _saveAuthData(response);
          _startTokenCheckTimer();
          _status = AuthStatus.authenticated;
        } catch (e) {
          // Yenileme başarısız - çıkış yap
          await _clearAuthData();
          _status = AuthStatus.unauthenticated;
        }
      } else {
        // Token geçerli - kullanıcı bilgilerini al
        _user = await _storage.getUser();
        if (_user == null) {
          try {
            _user = await _authService.getCurrentUser();
            await _storage.saveUser(_user!);
          } catch (e) {
            await _clearAuthData();
            _status = AuthStatus.unauthenticated;
            notifyListeners();
            return;
          }
        }
        _startTokenCheckTimer();
        _status = AuthStatus.authenticated;
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Oturum kontrolü hatası: $e');
      }
      _status = AuthStatus.unauthenticated;
    }
    
    notifyListeners();
  }
  
  /// Giriş yap
  Future<bool> login(String email, String password) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final response = await _authService.login(email, password);
      await _saveAuthData(response);
      
      // Push token kaydet
      await _registerPushToken();
      
      _startTokenCheckTimer();
      _status = AuthStatus.authenticated;
      notifyListeners();
      
      return true;
    } catch (e) {
      _errorMessage = _parseError(e);
      _status = AuthStatus.error;
      notifyListeners();
      return false;
    }
  }
  
  /// Çıkış yap
  Future<void> logout() async {
    _status = AuthStatus.loading;
    notifyListeners();
    
    try {
      // Push token sil
      final pushToken = _pushService.getPushToken();
      if (pushToken != null) {
        await _authService.unregisterPushToken(pushToken);
      }
      
      await _authService.logout();
    } catch (e) {
      // Hata olsa bile devam et
    }
    
    await _clearAuthData();
    _stopTokenCheckTimer();
    
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
  
  /// Token süresi dolduğunda çağrılır
  void onTokenExpired() {
    _clearAuthData();
    _stopTokenCheckTimer();
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
  
  /// Auth verilerini kaydet
  Future<void> _saveAuthData(AuthResponse response) async {
    await _storage.saveAccessToken(response.accessToken);
    await _storage.saveUser(response.user);
    _user = response.user;
  }
  
  /// Auth verilerini temizle
  Future<void> _clearAuthData() async {
    await _storage.clearSession();
    _user = null;
  }
  
  /// Push token kaydet
  Future<void> _registerPushToken() async {
    try {
      final pushToken = _pushService.getPushToken();
      if (pushToken != null) {
        await _authService.registerPushToken(pushToken);
      }
    } catch (e) {
      if (kDebugMode) {
        print('⚠️ Push token kayıt hatası: $e');
      }
    }
  }
  
  /// Token kontrolü zamanlayıcısını başlat
  void _startTokenCheckTimer() {
    _stopTokenCheckTimer();
    
    // Her 5 dakikada bir token kontrolü
    _tokenCheckTimer = Timer.periodic(
      const Duration(minutes: 5),
      (_) => _checkTokenExpiry(),
    );
  }
  
  /// Token kontrolü zamanlayıcısını durdur
  void _stopTokenCheckTimer() {
    _tokenCheckTimer?.cancel();
    _tokenCheckTimer = null;
  }
  
  /// Token süresini kontrol et
  Future<void> _checkTokenExpiry() async {
    try {
      final token = await _storage.getAccessToken();
      if (token == null) return;
      
      // Token süresi 5 dakika içinde dolacaksa yenile
      final expiryDate = JwtDecoder.getExpirationDate(token);
      final now = DateTime.now();
      final difference = expiryDate.difference(now);
      
      if (difference.inMinutes <= 5) {
        if (kDebugMode) {
          print('🔄 Token yenileniyor...');
        }
        
        try {
          final response = await _authService.refreshToken();
          await _saveAuthData(response);
        } catch (e) {
          onTokenExpired();
        }
      }
    } catch (e) {
      // Token kontrol hatası
    }
  }
  
  /// Hata mesajını parse et
  String _parseError(dynamic error) {
    if (error.toString().contains('401')) {
      return 'Incorrect email or password';
    }
    if (error.toString().contains('403')) {
      return 'Your account has been disabled';
    }
    if (error.toString().contains('network')) {
      return 'No internet connection';
    }
    return 'Sign-in failed. Please try again.';
  }
  
  @override
  void dispose() {
    _stopTokenCheckTimer();
    super.dispose();
  }
}
