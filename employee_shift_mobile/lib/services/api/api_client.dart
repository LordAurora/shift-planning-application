import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../../core/config/app_config.dart';
import '../storage_service.dart';

/// HTTP istemcisi - Otomatik token yönetimi ve hata işleme
class ApiClient {
  late final Dio _dio;
  final StorageService _storage;
  
  // Token yenileme callback'i
  Function()? onTokenExpired;
  
  ApiClient({required StorageService storage}) : _storage = storage {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: Duration(seconds: AppConfig.connectionTimeout),
        receiveTimeout: Duration(seconds: AppConfig.receiveTimeout),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
    
    _setupInterceptors();
  }
  
  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Otomatik token ekleme
          final token = await _storage.getAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          
          if (kDebugMode) {
            print('📤 REQUEST: ${options.method} ${options.path}');
          }
          
          handler.next(options);
        },
        onResponse: (response, handler) {
          if (kDebugMode) {
            print('📥 RESPONSE: ${response.statusCode} ${response.requestOptions.path}');
          }
          handler.next(response);
        },
        onError: (error, handler) async {
          if (kDebugMode) {
            print('❌ ERROR: ${error.response?.statusCode} ${error.requestOptions.path}');
            print('   Message: ${error.message}');
          }
          
          // 401 Unauthorized - Token süresi dolmuş
          if (error.response?.statusCode == 401) {
            // Token yenilemeyi dene
            final refreshed = await _tryRefreshToken();
            if (refreshed) {
              // İsteği tekrar dene
              try {
                final response = await _retryRequest(error.requestOptions);
                return handler.resolve(response);
              } catch (e) {
                return handler.next(error);
              }
            } else {
              // Token yenilemesi başarısız - oturumu sonlandır
              onTokenExpired?.call();
            }
          }
          
          handler.next(error);
        },
      ),
    );
  }
  
  /// Token yenileme işlemi
  Future<bool> _tryRefreshToken() async {
    try {
      final token = await _storage.getAccessToken();
      if (token == null) return false;
      
      final response = await Dio(
        BaseOptions(
          baseUrl: AppConfig.apiBaseUrl,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $token',
          },
        ),
      ).post('/auth/refresh');
      
      if (response.statusCode == 200) {
        final newToken = response.data['access_token'] as String;
        await _storage.saveAccessToken(newToken);
        return true;
      }
    } catch (e) {
      if (kDebugMode) {
        print('🔄 Token yenileme başarısız: $e');
      }
    }
    return false;
  }
  
  /// Başarısız isteği tekrar dene
  Future<Response<dynamic>> _retryRequest(RequestOptions requestOptions) async {
    final token = await _storage.getAccessToken();
    final options = Options(
      method: requestOptions.method,
      headers: {
        ...requestOptions.headers,
        'Authorization': 'Bearer $token',
      },
    );
    
    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }
  
  // HTTP metodları
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.get<T>(path, queryParameters: queryParameters, options: options);
  }
  
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.post<T>(path, data: data, queryParameters: queryParameters, options: options);
  }
  
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.put<T>(path, data: data, queryParameters: queryParameters, options: options);
  }
  
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.delete<T>(path, data: data, queryParameters: queryParameters, options: options);
  }
  
  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _dio.patch<T>(path, data: data, queryParameters: queryParameters, options: options);
  }
}
