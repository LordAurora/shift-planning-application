/// API endpoint'leri - Backend ile uyumlu
class ApiEndpoints {
  // Auth
  static const String login = '/auth/login';
  static const String logout = '/auth/logout';
  static const String refreshToken = '/auth/refresh';
  static const String me = '/auth/me';
  static const String register = '/auth/register';
  
  // Shifts
  static const String shifts = '/shifts';
  static String shiftById(int id) => '/shifts/$id';
  static const String myShifts = '/shifts/my';
  static String weeklyShifts(String startDate, String endDate) => 
      '/shifts?start_date=$startDate&end_date=$endDate';
  
  // Employees
  static const String employees = '/employees';
  static String employeeById(int id) => '/employees/$id';
  static const String myPreferences = '/employees/me/preferences';
  
  // Departments
  static const String departments = '/departments';
  static String departmentById(int id) => '/departments/$id';
  
  // Notifications
  static const String notifications = '/notifications';
  static String notificationById(int id) => '/notifications/$id';
  static String markAsRead(int id) => '/notifications/$id/read';
  static const String markAllAsRead = '/notifications/read-all';
  
  // Leave Requests (İzin Talepleri)
  static const String leaveRequests = '/leave-requests';
  static String leaveRequestById(int id) => '/leave-requests/$id';
  static const String myLeaveRequests = '/leave-requests/my';
  
  // Push Token
  static const String registerPushToken = '/push/register';
  static const String unregisterPushToken = '/push/unregister';
}
