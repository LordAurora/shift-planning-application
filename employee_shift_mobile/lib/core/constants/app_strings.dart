/// Uygulama metin sabitleri - Türkçe
class AppStrings {
  // Uygulama
  static const String appName = 'ShiftMaster';
  static const String appTagline = 'Vardiya Yönetim Sistemi';
  
  // Genel
  static const String loading = 'Yükleniyor...';
  static const String retry = 'Tekrar Dene';
  static const String cancel = 'İptal';
  static const String confirm = 'Onayla';
  static const String save = 'Kaydet';
  static const String delete = 'Sil';
  static const String edit = 'Düzenle';
  static const String close = 'Kapat';
  static const String ok = 'Tamam';
  static const String yes = 'Evet';
  static const String no = 'Hayır';
  
  // Giriş
  static const String login = 'Giriş Yap';
  static const String logout = 'Çıkış Yap';
  static const String email = 'E-posta';
  static const String password = 'Şifre';
  static const String forgotPassword = 'Şifremi Unuttum';
  static const String welcomeBack = 'Tekrar Hoş Geldiniz';
  static const String loginSubtitle = 'Devam etmek için giriş yapın';
  
  // Ana Sayfa
  static const String home = 'Ana Sayfa';
  static const String todayShift = 'Bugünkü Vardiya';
  static const String upcomingShifts = 'Yaklaşan Vardiyalar';
  static const String noShiftToday = 'Bugün vardiya yok';
  static const String greeting = 'Merhaba';
  
  // Vardiyalar
  static const String shifts = 'Vardiyalar';
  static const String weeklySchedule = 'Haftalık Vardiya';
  static const String myShifts = 'Vardiyalarım';
  static const String shiftDetails = 'Vardiya Detayları';
  static const String startTime = 'Başlangıç';
  static const String endTime = 'Bitiş';
  static const String duration = 'Süre';
  static const String department = 'Departman';
  static const String location = 'Lokasyon';
  
  // Vardiya Durumları
  static const String scheduled = 'Planlandı';
  static const String completed = 'Tamamlandı';
  static const String cancelled = 'İptal Edildi';
  
  // İzin Talepleri
  static const String leaveRequests = 'İzin Talepleri';
  static const String newLeaveRequest = 'Yeni İzin Talebi';
  static const String myLeaveRequests = 'İzin Taleplerim';
  static const String leaveType = 'İzin Türü';
  static const String startDate = 'Başlangıç Tarihi';
  static const String endDate = 'Bitiş Tarihi';
  static const String reason = 'Gerekçe';
  
  // İzin Durumları
  static const String pending = 'Beklemede';
  static const String approved = 'Onaylandı';
  static const String rejected = 'Reddedildi';
  
  // Bildirimler
  static const String notifications = 'Bildirimler';
  static const String noNotifications = 'Bildirim yok';
  static const String markAllRead = 'Tümünü Okundu İşaretle';
  
  // Profil
  static const String profile = 'Profil';
  static const String personalInfo = 'Kişisel Bilgiler';
  static const String settings = 'Ayarlar';
  static const String about = 'Hakkında';
  static const String version = 'Versiyon';
  
  // Hatalar
  static const String error = 'Hata';
  static const String networkError = 'İnternet bağlantısı yok';
  static const String networkErrorDesc = 'Lütfen internet bağlantınızı kontrol edin';
  static const String serverError = 'Sunucu hatası oluştu';
  static const String sessionExpired = 'Oturumunuz sona erdi';
  static const String sessionExpiredDesc = 'Lütfen tekrar giriş yapın';
  static const String unknownError = 'Beklenmeyen bir hata oluştu';
  static const String invalidCredentials = 'E-posta veya şifre hatalı';
  
  // Başarı Mesajları
  static const String success = 'Başarılı';
  static const String loginSuccess = 'Giriş başarılı';
  static const String logoutSuccess = 'Çıkış yapıldı';
  static const String leaveRequestCreated = 'İzin talebi oluşturuldu';
  static const String dataRefreshed = 'Veriler güncellendi';
  
  // Günler
  static const List<String> weekDays = [
    'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'
  ];
  
  static const List<String> weekDaysShort = [
    'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'
  ];
  
  // Aylar
  static const List<String> months = [
    'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
    'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
  ];
}
