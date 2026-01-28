import '../../core/config/api_endpoints.dart';
import '../../data/models/user_model.dart';
import 'api_client.dart';

/// Kimlik doğrulama servisi
class AuthService {
  final ApiClient _client;
  
  AuthService({required ApiClient client}) : _client = client;
  
  /// Giriş yap
  Future<AuthResponse> login(String email, String password) async {
    final response = await _client.post(
      ApiEndpoints.login,
      data: LoginRequest(email: email, password: password).toJson(),
    );
    
    return AuthResponse.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// Çıkış yap
  Future<void> logout() async {
    try {
      await _client.post(ApiEndpoints.logout);
    } catch (e) {
      // Logout hatası olsa bile devam et
    }
  }
  
  /// Token yenile
  Future<AuthResponse> refreshToken() async {
    final response = await _client.post(ApiEndpoints.refreshToken);
    return AuthResponse.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// Mevcut kullanıcı bilgilerini al
  Future<User> getCurrentUser() async {
    final response = await _client.get(ApiEndpoints.me);
    return User.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// Push token kaydet (Backend'e)
  Future<void> registerPushToken(String pushToken) async {
    await _client.post(
      ApiEndpoints.registerPushToken,
      data: {'push_token': pushToken, 'platform': 'android'},
    );
  }
  
  /// Push token sil
  Future<void> unregisterPushToken(String pushToken) async {
    await _client.post(
      ApiEndpoints.unregisterPushToken,
      data: {'push_token': pushToken},
    );
  }
}
