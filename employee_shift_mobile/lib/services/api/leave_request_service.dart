import '../../core/config/api_endpoints.dart';
import '../../data/models/leave_request_model.dart';
import 'api_client.dart';

/// İzin talebi servisi
class LeaveRequestService {
  final ApiClient _client;
  
  LeaveRequestService({required ApiClient client}) : _client = client;
  
  /// İzin taleplerini getir
  Future<List<LeaveRequest>> getLeaveRequests({
    LeaveStatus? status,
    int page = 1,
    int pageSize = 20,
  }) async {
    final queryParams = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
    };
    
    if (status != null) {
      queryParams['status'] = status.value;
    }
    
    final response = await _client.get(
      ApiEndpoints.leaveRequests,
      queryParameters: queryParams,
    );
    
    if (response.data is Map && response.data['items'] != null) {
      final items = response.data['items'] as List<dynamic>;
      return items
          .map((item) => LeaveRequest.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    
    final items = response.data as List<dynamic>;
    return items
        .map((item) => LeaveRequest.fromJson(item as Map<String, dynamic>))
        .toList();
  }
  
  /// Kendi izin taleplerimi getir
  Future<List<LeaveRequest>> getMyLeaveRequests() async {
    final response = await _client.get(ApiEndpoints.myLeaveRequests);
    
    if (response.data is Map && response.data['items'] != null) {
      final items = response.data['items'] as List<dynamic>;
      return items
          .map((item) => LeaveRequest.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    
    final items = response.data as List<dynamic>;
    return items
        .map((item) => LeaveRequest.fromJson(item as Map<String, dynamic>))
        .toList();
  }
  
  /// Tek izin talebi getir
  Future<LeaveRequest> getLeaveRequestById(int id) async {
    final response = await _client.get(ApiEndpoints.leaveRequestById(id));
    return LeaveRequest.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// Yeni izin talebi oluştur
  Future<LeaveRequest> createLeaveRequest(CreateLeaveRequest request) async {
    final response = await _client.post(
      ApiEndpoints.leaveRequests,
      data: request.toJson(),
    );
    return LeaveRequest.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// İzin talebini iptal et
  Future<void> cancelLeaveRequest(int id) async {
    await _client.delete(ApiEndpoints.leaveRequestById(id));
  }
  
  /// Bekleyen izin taleplerini getir
  Future<List<LeaveRequest>> getPendingRequests() async {
    return getLeaveRequests(status: LeaveStatus.pending);
  }
}
