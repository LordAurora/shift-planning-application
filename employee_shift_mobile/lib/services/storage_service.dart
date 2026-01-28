import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../../data/models/user_model.dart';

/// Güvenli depolama servisi - Token ve kullanıcı bilgileri
class StorageService {
  static const String _accessTokenKey = 'access_token';
  static const String _userKey = 'current_user';
  static const String _pushTokenKey = 'push_token';
  static const String _isFirstLaunchKey = 'is_first_launch';
  static const String _lastSyncTimeKey = 'last_sync_time';
  
  final FlutterSecureStorage _secureStorage;
  late SharedPreferences _prefs;
  
  StorageService() : _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
  );
  
  /// Servisi başlat
  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }
  
  // === Token Yönetimi ===
  
  /// Access token kaydet
  Future<void> saveAccessToken(String token) async {
    await _secureStorage.write(key: _accessTokenKey, value: token);
  }
  
  /// Access token al
  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: _accessTokenKey);
  }
  
  /// Access token sil
  Future<void> deleteAccessToken() async {
    await _secureStorage.delete(key: _accessTokenKey);
  }
  
  /// Token var mı kontrolü
  Future<bool> hasAccessToken() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }
  
  // === Kullanıcı Bilgileri ===
  
  /// Kullanıcı bilgilerini kaydet
  Future<void> saveUser(User user) async {
    final userJson = jsonEncode(user.toJson());
    await _secureStorage.write(key: _userKey, value: userJson);
  }
  
  /// Kullanıcı bilgilerini al
  Future<User?> getUser() async {
    final userJson = await _secureStorage.read(key: _userKey);
    if (userJson == null) return null;
    
    try {
      final userMap = jsonDecode(userJson) as Map<String, dynamic>;
      return User.fromJson(userMap);
    } catch (e) {
      return null;
    }
  }
  
  /// Kullanıcı bilgilerini sil
  Future<void> deleteUser() async {
    await _secureStorage.delete(key: _userKey);
  }
  
  // === Push Token ===
  
  /// Push token kaydet
  Future<void> savePushToken(String token) async {
    await _prefs.setString(_pushTokenKey, token);
  }
  
  /// Push token al
  String? getPushToken() {
    return _prefs.getString(_pushTokenKey);
  }
  
  /// Push token sil
  Future<void> deletePushToken() async {
    await _prefs.remove(_pushTokenKey);
  }
  
  // === İlk Açılış Kontrolü ===
  
  /// İlk açılış mı?
  bool get isFirstLaunch {
    return _prefs.getBool(_isFirstLaunchKey) ?? true;
  }
  
  /// İlk açılışı işaretle
  Future<void> setFirstLaunchComplete() async {
    await _prefs.setBool(_isFirstLaunchKey, false);
  }
  
  // === Senkronizasyon Zamanı ===
  
  /// Son senkronizasyon zamanını kaydet
  Future<void> saveLastSyncTime(String key, DateTime time) async {
    await _prefs.setString('${_lastSyncTimeKey}_$key', time.toIso8601String());
  }
  
  /// Son senkronizasyon zamanını al
  DateTime? getLastSyncTime(String key) {
    final timeStr = _prefs.getString('${_lastSyncTimeKey}_$key');
    if (timeStr == null) return null;
    return DateTime.tryParse(timeStr);
  }
  
  // === Temizleme ===
  
  /// Tüm verileri temizle (çıkış yapma)
  Future<void> clearAll() async {
    await _secureStorage.deleteAll();
    // Push token ve bazı ayarları koru
    final pushToken = getPushToken();
    await _prefs.clear();
    if (pushToken != null) {
      await savePushToken(pushToken);
    }
  }
  
  /// Oturum verilerini temizle
  Future<void> clearSession() async {
    await deleteAccessToken();
    await deleteUser();
  }
}
