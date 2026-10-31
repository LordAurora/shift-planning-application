import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:intl/date_symbol_data_local.dart';

// Core
import 'core/theme/app_theme.dart';
import 'core/constants/app_strings.dart';

// Services
import 'services/storage_service.dart';
import 'services/connectivity_service.dart';
import 'services/push_notification_service.dart';
import 'services/api/api_client.dart';
import 'services/api/auth_service.dart';
import 'services/api/shift_service.dart';
import 'services/api/notification_service.dart';
import 'services/api/leave_request_service.dart';

// Providers
import 'providers/auth_provider.dart';
import 'providers/shift_provider.dart';
import 'providers/notification_provider.dart';
import 'providers/leave_request_provider.dart';

// Screens
import 'presentation/screens/screens.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Türkçe tarih formatı için
  await initializeDateFormatting('en_US', null);
  
  // Sistem UI ayarları
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  
  // Dikey yönlendirme kilidi
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  // Servisleri başlat
  final storageService = StorageService();
  await storageService.init();
  
  final connectivityService = ConnectivityService();
  await connectivityService.init();
  
  final pushNotificationService = PushNotificationService(storage: storageService);
  await pushNotificationService.init();
  
  runApp(
    ShiftMasterApp(
      storageService: storageService,
      connectivityService: connectivityService,
      pushNotificationService: pushNotificationService,
    ),
  );
}

/// Ana Uygulama Widget'ı
class ShiftMasterApp extends StatefulWidget {
  final StorageService storageService;
  final ConnectivityService connectivityService;
  final PushNotificationService pushNotificationService;

  const ShiftMasterApp({
    super.key,
    required this.storageService,
    required this.connectivityService,
    required this.pushNotificationService,
  });

  @override
  State<ShiftMasterApp> createState() => _ShiftMasterAppState();
}

class _ShiftMasterAppState extends State<ShiftMasterApp> with WidgetsBindingObserver {
  late ApiClient _apiClient;
  late AuthService _authService;
  late ShiftService _shiftService;
  late NotificationService _notificationService;
  late LeaveRequestService _leaveRequestService;
  
  late AuthProvider _authProvider;
  late ShiftProvider _shiftProvider;
  late NotificationProvider _notificationProvider;
  late LeaveRequestProvider _leaveRequestProvider;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeServices();
    _setupPushNotifications();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _shiftProvider.stopAutoSync();
    _notificationProvider.stopAutoSync();
    _leaveRequestProvider.stopAutoSync();
    widget.connectivityService.dispose();
    super.dispose();
  }

  /// Uygulama yaşam döngüsü değişikliklerini dinle
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    if (state == AppLifecycleState.resumed) {
      // Uygulama ön plana geldiğinde otomatik senkronizasyon
      if (_authProvider.isAuthenticated) {
        _shiftProvider.refreshAll();
        _notificationProvider.refreshNotifications();
        _leaveRequestProvider.refreshRequests();
      }
    } else if (state == AppLifecycleState.paused) {
      // Uygulama arka plana geçtiğinde - gerekirse işlemler
    }
  }

  /// Servisleri ve Provider'ları başlat
  void _initializeServices() {
    // API Client
    _apiClient = ApiClient(storage: widget.storageService);
    
    // API Services
    _authService = AuthService(client: _apiClient);
    _shiftService = ShiftService(client: _apiClient);
    _notificationService = NotificationService(client: _apiClient);
    _leaveRequestService = LeaveRequestService(client: _apiClient);
    
    // Providers
    _authProvider = AuthProvider(
      authService: _authService,
      storage: widget.storageService,
      pushService: widget.pushNotificationService,
    );
    
    _shiftProvider = ShiftProvider(
      shiftService: _shiftService,
      connectivityService: widget.connectivityService,
    );
    
    _notificationProvider = NotificationProvider(
      notificationService: _notificationService,
      connectivityService: widget.connectivityService,
    );
    
    _leaveRequestProvider = LeaveRequestProvider(
      leaveService: _leaveRequestService,
      connectivityService: widget.connectivityService,
    );
    
    // Token süresi dolduğunda callback
    _apiClient.onTokenExpired = () {
      _authProvider.onTokenExpired();
    };
  }

  /// Push bildirim işleyicilerini ayarla
  void _setupPushNotifications() {
    // Bildirim tıklandığında deep link yönlendirmesi
    widget.pushNotificationService.onNotificationTapped = (route, data) {
      if (route != null && _authProvider.isAuthenticated) {
        // Route'a göre yönlendirme yapılacak
        // Navigator ile ilgili ekrana git
      }
    };
    
    // Uygulama açıkken bildirim alındığında
    widget.pushNotificationService.onNotificationReceived = (title, body, data) {
      // Verileri otomatik yenile
      _shiftProvider.refreshAll();
      _notificationProvider.refreshNotifications();
      _leaveRequestProvider.refreshRequests();
    };
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Services
        Provider<StorageService>.value(value: widget.storageService),
        Provider<ConnectivityService>.value(value: widget.connectivityService),
        Provider<PushNotificationService>.value(value: widget.pushNotificationService),
        
        // Providers
        ChangeNotifierProvider<AuthProvider>.value(value: _authProvider),
        ChangeNotifierProvider<ShiftProvider>.value(value: _shiftProvider),
        ChangeNotifierProvider<NotificationProvider>.value(value: _notificationProvider),
        ChangeNotifierProvider<LeaveRequestProvider>.value(value: _leaveRequestProvider),
      ],
      child: MaterialApp(
        title: AppStrings.appName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const AppRouter(),
        routes: {
          '/login': (context) => const LoginScreen(),
          '/home': (context) => const MainShell(),
          '/shifts/weekly': (context) => const WeeklyShiftsScreen(),
          '/notifications': (context) => const NotificationsScreen(),
          '/leave-requests': (context) => const LeaveRequestsScreen(),
          '/profile': (context) => const ProfileScreen(),
        },
      ),
    );
  }
}

/// Uygulama Router - Otomatik oturum kontrolü ve yönlendirme
class AppRouter extends StatefulWidget {
  const AppRouter({super.key});

  @override
  State<AppRouter> createState() => _AppRouterState();
}

class _AppRouterState extends State<AppRouter> {
  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    // Otomatik oturum kontrolü
    await context.read<AuthProvider>().checkAuthStatus();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, _) {
        switch (authProvider.status) {
          case AuthStatus.initial:
          case AuthStatus.loading:
            return const SplashScreen();
          
          case AuthStatus.authenticated:
            // Otomatik senkronizasyonları başlat
            WidgetsBinding.instance.addPostFrameCallback((_) {
              _startAutoSync();
            });
            return const MainShell();
          
          case AuthStatus.unauthenticated:
          case AuthStatus.error:
            return const LoginScreen();
        }
      },
    );
  }

  void _startAutoSync() {
    // Tüm provider'lar için otomatik senkronizasyonu başlat
    context.read<ShiftProvider>().startAutoSync();
    context.read<NotificationProvider>().startAutoSync();
    context.read<LeaveRequestProvider>().startAutoSync();
    
    // İlk veri yüklemesi
    final user = context.read<AuthProvider>().user;
    if (user != null) {
      context.read<ShiftProvider>().loadInitialData(employeeId: user.id);
      context.read<NotificationProvider>().fetchNotifications();
      context.read<LeaveRequestProvider>().fetchMyRequests();
    }
  }
}
