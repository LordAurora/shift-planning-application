import '../../core/config/api_endpoints.dart';
import 'api_client.dart';

/// Scheduling preferences of the signed-in employee.
///
/// The backend stores the weekly day off as 0-6 (Sunday-Saturday);
/// the app works with lowercase day names.
class EmployeePreferences {
  static const List<String> dayKeys = [
    'sunday',
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
  ];

  final String preferredShift; // morning | day | afternoon | night | flexible
  final String weeklyOffDay; // monday ... sunday
  final String workModel; // office | remote | hybrid
  final int officeDays;
  final int remoteDays;
  final String notes;

  const EmployeePreferences({
    this.preferredShift = 'morning',
    this.weeklyOffDay = 'saturday',
    this.workModel = 'hybrid',
    this.officeDays = 3,
    this.remoteDays = 2,
    this.notes = '',
  });

  factory EmployeePreferences.fromJson(Map<String, dynamic> json) {
    final offDay = json['weekly_off_day'];
    return EmployeePreferences(
      preferredShift: (json['preferred_shift'] as String?) ?? 'flexible',
      weeklyOffDay: offDay is int && offDay >= 0 && offDay < 7 ? dayKeys[offDay] : 'saturday',
      workModel: (json['work_model'] as String?) ?? 'hybrid',
      officeDays: (json['office_days'] as int?) ?? 3,
      remoteDays: (json['remote_days'] as int?) ?? 2,
      notes: (json['notes'] as String?) ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        // "flexible" means no specific preference for the optimizer
        'preferred_shift': preferredShift == 'flexible' ? null : preferredShift,
        'weekly_off_day': dayKeys.indexOf(weeklyOffDay),
        'work_model': workModel,
        'office_days': officeDays,
        'remote_days': remoteDays,
        'notes': notes,
      };
}

class PreferencesService {
  final ApiClient _client;

  PreferencesService({required ApiClient client}) : _client = client;

  Future<EmployeePreferences> getMyPreferences() async {
    final response = await _client.get(ApiEndpoints.myPreferences);
    return EmployeePreferences.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<EmployeePreferences> saveMyPreferences(EmployeePreferences preferences) async {
    final response = await _client.put(ApiEndpoints.myPreferences, data: preferences.toJson());
    return EmployeePreferences.fromJson(Map<String, dynamic>.from(response.data as Map));
  }
}
