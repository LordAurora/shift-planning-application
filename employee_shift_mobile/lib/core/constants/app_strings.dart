/// User-facing text constants
class AppStrings {
  // Uygulama
  static const String appName = 'ShiftMaster AI';
  static const String appTagline = 'AI-assisted shift planning';
  
  // Genel
  static const String loading = 'Loading...';
  static const String retry = 'Try again';
  static const String cancel = 'Cancel';
  static const String confirm = 'Confirm';
  static const String save = 'Save';
  static const String delete = 'Delete';
  static const String edit = 'Edit';
  static const String close = 'Close';
  static const String ok = 'OK';
  static const String yes = 'Yes';
  static const String no = 'No';
  
  // Giriş
  static const String login = 'Sign in';
  static const String logout = 'Sign out';
  static const String email = 'Email';
  static const String password = 'Password';
  static const String forgotPassword = 'Forgot password?';
  static const String welcomeBack = 'Welcome back';
  static const String loginSubtitle = 'Sign in to continue';
  
  // Ana Sayfa
  static const String home = 'Home';
  static const String todayShift = 'Shift today';
  static const String upcomingShifts = 'Upcoming shifts';
  static const String noShiftToday = 'No shift today';
  static const String greeting = 'Hello';
  
  // Vardiyalar
  static const String shifts = 'Shifts';
  static const String weeklySchedule = 'Weekly schedule';
  static const String myShifts = 'My shifts';
  static const String shiftDetails = 'Shift details';
  static const String startTime = 'Start';
  static const String endTime = 'End';
  static const String duration = 'Duration';
  static const String department = 'Department';
  static const String location = 'Location';
  
  // Vardiya Durumları
  static const String scheduled = 'Scheduled';
  static const String completed = 'Completed';
  static const String cancelled = 'Cancelled';
  
  // İzin Talepleri
  static const String leaveRequests = 'Leave requests';
  static const String newLeaveRequest = 'New leave request';
  static const String myLeaveRequests = 'My leave requests';
  static const String leaveType = 'Leave type';
  static const String startDate = 'Start date';
  static const String endDate = 'End date';
  static const String reason = 'Reason';
  
  // İzin Durumları
  static const String pending = 'Pending';
  static const String approved = 'Approved';
  static const String rejected = 'Rejected';
  
  // Bildirimler
  static const String notifications = 'Notifications';
  static const String noNotifications = 'No notifications';
  static const String markAllRead = 'Mark all as read';
  
  // Profil
  static const String profile = 'Profile';
  static const String personalInfo = 'Personal information';
  static const String settings = 'Settings';
  static const String about = 'About';
  static const String version = 'Version';
  
  // Hatalar
  static const String error = 'Error';
  static const String networkError = 'No internet connection';
  static const String networkErrorDesc = 'Please check your internet connection';
  static const String serverError = 'A server error occurred';
  static const String sessionExpired = 'Your session has expired';
  static const String sessionExpiredDesc = 'Please sign in again';
  static const String unknownError = 'An unexpected error occurred';
  static const String invalidCredentials = 'Incorrect email or password';
  
  // Başarı Mesajları
  static const String success = 'Success';
  static const String loginSuccess = 'Signed in';
  static const String logoutSuccess = 'Signed out';
  static const String leaveRequestCreated = 'Leave request created';
  static const String dataRefreshed = 'Data refreshed';
  
  // Günler
  static const List<String> weekDays = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
  ];
  
  static const List<String> weekDaysShort = [
    'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'
  ];
  
  // Aylar
  static const List<String> months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
}
