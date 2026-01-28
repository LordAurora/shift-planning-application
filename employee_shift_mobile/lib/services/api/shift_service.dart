import '../../core/config/api_endpoints.dart';
import '../../data/models/shift_model.dart';
import 'api_client.dart';

/// Vardiya servisi
class ShiftService {
  final ApiClient _client;
  
  ShiftService({required ApiClient client}) : _client = client;
  
  /// Vardiyaları getir
  Future<ShiftListResponse> getShifts({
    int page = 1,
    int pageSize = 20,
    DateTime? startDate,
    DateTime? endDate,
    int? employeeId,
    int? departmentId,
  }) async {
    final queryParams = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
    };
    
    if (startDate != null) {
      queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
    }
    if (endDate != null) {
      queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
    }
    if (employeeId != null) {
      queryParams['employee_id'] = employeeId;
    }
    if (departmentId != null) {
      queryParams['department_id'] = departmentId;
    }
    
    final response = await _client.get(
      ApiEndpoints.shifts,
      queryParameters: queryParams,
    );
    
    return ShiftListResponse.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// Tek vardiya getir
  Future<Shift> getShiftById(int id) async {
    final response = await _client.get(ApiEndpoints.shiftById(id));
    return Shift.fromJson(response.data as Map<String, dynamic>);
  }
  
  /// Haftalık vardiyaları getir
  Future<List<Shift>> getWeeklyShifts({
    required DateTime weekStart,
    int? employeeId,
  }) async {
    final weekEnd = weekStart.add(const Duration(days: 6));
    
    final response = await getShifts(
      startDate: weekStart,
      endDate: weekEnd,
      employeeId: employeeId,
      pageSize: 100, // Haftalık tüm vardiyaları al
    );
    
    return response.items;
  }
  
  /// Bugünkü vardiyaları getir
  Future<List<Shift>> getTodayShifts({int? employeeId}) async {
    final today = DateTime.now();
    final startOfDay = DateTime(today.year, today.month, today.day);
    final endOfDay = startOfDay.add(const Duration(days: 1));
    
    final response = await getShifts(
      startDate: startOfDay,
      endDate: endOfDay,
      employeeId: employeeId,
    );
    
    return response.items;
  }
  
  /// Yaklaşan vardiyaları getir
  Future<List<Shift>> getUpcomingShifts({
    int? employeeId,
    int limit = 5,
  }) async {
    final now = DateTime.now();
    final futureDate = now.add(const Duration(days: 30));
    
    final response = await getShifts(
      startDate: now,
      endDate: futureDate,
      employeeId: employeeId,
      pageSize: limit,
    );
    
    return response.items
        .where((s) => s.status == ShiftStatus.scheduled && s.isUpcoming)
        .take(limit)
        .toList();
  }
}
