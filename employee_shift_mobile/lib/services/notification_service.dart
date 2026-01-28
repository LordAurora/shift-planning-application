import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart' show TimeOfDay, Color;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz_data;

/// Enhanced notification service with push governance.
/// Handles notification priority, quiet hours, batching, and preferences.
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  
  FirebaseMessaging? _firebaseMessaging;
  
  // Stream controllers
  final _notificationController = StreamController<NotificationPayload>.broadcast();
  Stream<NotificationPayload> get onNotification => _notificationController.stream;
  
  // Notification settings
  NotificationSettings _settings = NotificationSettings();
  
  // Notification batching
  final List<NotificationPayload> _pendingNotifications = [];
  Timer? _batchTimer;
  static const Duration _batchDelay = Duration(seconds: 3);

  /// Initialize notification service
  Future<void> initialize() async {
    // Initialize timezone
    tz_data.initializeTimeZones();
    
    // Load settings
    await _loadSettings();
    
    // Initialize local notifications
    await _initializeLocalNotifications();
    
    // Initialize Firebase Messaging (if available)
    await _initializeFirebaseMessaging();
  }

  /// Initialize local notifications
  Future<void> _initializeLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );
    
    // Request permissions on iOS
    if (Platform.isIOS) {
      await _localNotifications
          .resolvePlatformSpecificImplementation<
              IOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(
            alert: true,
            badge: true,
            sound: true,
          );
    }
  }

  /// Initialize Firebase Messaging
  Future<void> _initializeFirebaseMessaging() async {
    try {
      _firebaseMessaging = FirebaseMessaging.instance;
      
      // Request permission
      final settings = await _firebaseMessaging!.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );
      
      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        // Get FCM token
        final token = await _firebaseMessaging!.getToken();
        debugPrint('FCM Token: $token');
        
        // Listen for token refresh
        _firebaseMessaging!.onTokenRefresh.listen((newToken) {
          debugPrint('FCM Token refreshed: $newToken');
          // Send to server
        });
        
        // Handle foreground messages
        FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
        
        // Handle background/terminated state messages
        FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
        
        // Check for initial message (app opened from notification)
        final initialMessage = await _firebaseMessaging!.getInitialMessage();
        if (initialMessage != null) {
          _handleNotificationTap(initialMessage);
        }
      }
    } catch (e) {
      debugPrint('Firebase Messaging initialization failed: $e');
    }
  }

  /// Handle foreground FCM message
  void _handleForegroundMessage(RemoteMessage message) {
    final payload = NotificationPayload.fromRemoteMessage(message);
    
    // Check if should show based on settings
    if (_shouldShowNotification(payload)) {
      _queueNotification(payload);
    }
  }

  /// Handle notification tap
  void _handleNotificationTap(RemoteMessage message) {
    final payload = NotificationPayload.fromRemoteMessage(message);
    _notificationController.add(payload);
  }

  /// Local notification tap handler
  void _onNotificationTapped(NotificationResponse response) {
    if (response.payload != null) {
      final payload = NotificationPayload.fromJson(
        jsonDecode(response.payload!),
      );
      _notificationController.add(payload);
    }
  }

  // ============== Notification Governance ==============

  /// Check if notification should be shown based on settings
  bool _shouldShowNotification(NotificationPayload payload) {
    // Check if notifications are enabled
    if (!_settings.enabled) return false;
    
    // Check notification type preference
    if (!_isTypeEnabled(payload.type)) return false;
    
    // Check quiet hours
    if (_isInQuietHours()) {
      // Allow critical notifications during quiet hours
      if (payload.priority != NotificationPriority.critical) {
        return false;
      }
    }
    
    // Check do not disturb
    if (_settings.doNotDisturb) {
      if (payload.priority != NotificationPriority.critical) {
        return false;
      }
    }
    
    return true;
  }

  /// Check if notification type is enabled
  bool _isTypeEnabled(NotificationType type) {
    switch (type) {
      case NotificationType.shiftAssigned:
      case NotificationType.shiftUpdated:
      case NotificationType.shiftCancelled:
        return _settings.shiftNotifications;
      case NotificationType.leaveApproved:
      case NotificationType.leaveRejected:
      case NotificationType.leaveReminder:
        return _settings.leaveNotifications;
      case NotificationType.schedulePublished:
      case NotificationType.scheduleChange:
        return _settings.scheduleNotifications;
      case NotificationType.reminder:
        return _settings.reminderNotifications;
      case NotificationType.announcement:
        return _settings.announcementNotifications;
      case NotificationType.system:
        return true; // System notifications always enabled
    }
  }

  /// Check if current time is within quiet hours
  bool _isInQuietHours() {
    if (!_settings.quietHoursEnabled) return false;
    
    final now = DateTime.now();
    final currentTime = TimeOfDay(hour: now.hour, minute: now.minute);
    
    final start = _settings.quietHoursStart;
    final end = _settings.quietHoursEnd;
    
    if (start.hour < end.hour || 
        (start.hour == end.hour && start.minute < end.minute)) {
      // Same day quiet hours (e.g., 22:00 - 07:00 next day doesn't apply)
      return _isTimeBetween(currentTime, start, end);
    } else {
      // Overnight quiet hours (e.g., 22:00 - 07:00)
      return !_isTimeBetween(currentTime, end, start);
    }
  }

  bool _isTimeBetween(TimeOfDay current, TimeOfDay start, TimeOfDay end) {
    final currentMinutes = current.hour * 60 + current.minute;
    final startMinutes = start.hour * 60 + start.minute;
    final endMinutes = end.hour * 60 + end.minute;
    
    return currentMinutes >= startMinutes && currentMinutes < endMinutes;
  }

  // ============== Notification Batching ==============

  /// Queue notification for batching
  void _queueNotification(NotificationPayload payload) {
    // Critical notifications are shown immediately
    if (payload.priority == NotificationPriority.critical) {
      _showLocalNotification(payload);
      return;
    }
    
    // Add to pending queue
    _pendingNotifications.add(payload);
    
    // Start batch timer if not running
    _batchTimer?.cancel();
    _batchTimer = Timer(_batchDelay, _processBatchedNotifications);
  }

  /// Process batched notifications
  void _processBatchedNotifications() {
    if (_pendingNotifications.isEmpty) return;
    
    if (_pendingNotifications.length == 1) {
      // Single notification - show normally
      _showLocalNotification(_pendingNotifications.first);
    } else {
      // Multiple notifications - show summary
      _showBatchedNotifications();
    }
    
    _pendingNotifications.clear();
  }

  /// Show batched notifications as summary
  void _showBatchedNotifications() {
    final count = _pendingNotifications.length;
    final types = _pendingNotifications.map((n) => n.type).toSet();
    
    String title;
    String body;
    
    if (types.length == 1) {
      // All same type
      title = '${count} new notifications';
      body = _pendingNotifications.map((n) => n.title).join('\n');
    } else {
      // Mixed types
      title = '${count} new notifications';
      body = 'You have new shift and schedule updates';
    }
    
    _showLocalNotification(NotificationPayload(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title,
      body: body,
      type: NotificationType.system,
      priority: NotificationPriority.normal,
      data: {'batched': true, 'count': count},
    ));
  }

  // ============== Display Methods ==============

  /// Show local notification
  Future<void> _showLocalNotification(NotificationPayload payload) async {
    final androidDetails = AndroidNotificationDetails(
      _getChannelId(payload.type),
      _getChannelName(payload.type),
      channelDescription: _getChannelDescription(payload.type),
      importance: _getImportance(payload.priority),
      priority: _getPriority(payload.priority),
      icon: '@mipmap/ic_launcher',
      color: const Color(0xFF1976D2),
    );
    
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    
    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.show(
      payload.id.hashCode,
      payload.title,
      payload.body,
      details,
      payload: jsonEncode(payload.toJson()),
    );
  }

  /// Schedule notification
  Future<void> scheduleNotification({
    required NotificationPayload payload,
    required DateTime scheduledTime,
  }) async {
    final androidDetails = AndroidNotificationDetails(
      _getChannelId(payload.type),
      _getChannelName(payload.type),
      importance: _getImportance(payload.priority),
      priority: _getPriority(payload.priority),
    );
    
    const iosDetails = DarwinNotificationDetails();
    
    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.zonedSchedule(
      payload.id.hashCode,
      payload.title,
      payload.body,
      tz.TZDateTime.from(scheduledTime, tz.local),
      details,
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      payload: jsonEncode(payload.toJson()),
    );
  }

  /// Cancel scheduled notification
  Future<void> cancelNotification(String id) async {
    await _localNotifications.cancel(id.hashCode);
  }

  /// Cancel all notifications
  Future<void> cancelAllNotifications() async {
    await _localNotifications.cancelAll();
  }

  // ============== Channel Helpers ==============

  String _getChannelId(NotificationType type) {
    switch (type) {
      case NotificationType.shiftAssigned:
      case NotificationType.shiftUpdated:
      case NotificationType.shiftCancelled:
        return 'shift_channel';
      case NotificationType.leaveApproved:
      case NotificationType.leaveRejected:
      case NotificationType.leaveReminder:
        return 'leave_channel';
      case NotificationType.schedulePublished:
      case NotificationType.scheduleChange:
        return 'schedule_channel';
      case NotificationType.reminder:
        return 'reminder_channel';
      case NotificationType.announcement:
        return 'announcement_channel';
      case NotificationType.system:
        return 'system_channel';
    }
  }

  String _getChannelName(NotificationType type) {
    switch (type) {
      case NotificationType.shiftAssigned:
      case NotificationType.shiftUpdated:
      case NotificationType.shiftCancelled:
        return 'Shift Notifications';
      case NotificationType.leaveApproved:
      case NotificationType.leaveRejected:
      case NotificationType.leaveReminder:
        return 'Leave Notifications';
      case NotificationType.schedulePublished:
      case NotificationType.scheduleChange:
        return 'Schedule Notifications';
      case NotificationType.reminder:
        return 'Reminders';
      case NotificationType.announcement:
        return 'Announcements';
      case NotificationType.system:
        return 'System Notifications';
    }
  }

  String _getChannelDescription(NotificationType type) {
    switch (type) {
      case NotificationType.shiftAssigned:
      case NotificationType.shiftUpdated:
      case NotificationType.shiftCancelled:
        return 'Notifications about your shift assignments';
      case NotificationType.leaveApproved:
      case NotificationType.leaveRejected:
      case NotificationType.leaveReminder:
        return 'Notifications about your leave requests';
      case NotificationType.schedulePublished:
      case NotificationType.scheduleChange:
        return 'Notifications about schedule changes';
      case NotificationType.reminder:
        return 'Shift and task reminders';
      case NotificationType.announcement:
        return 'Company announcements';
      case NotificationType.system:
        return 'System notifications';
    }
  }

  Importance _getImportance(NotificationPriority priority) {
    switch (priority) {
      case NotificationPriority.critical:
        return Importance.max;
      case NotificationPriority.high:
        return Importance.high;
      case NotificationPriority.normal:
        return Importance.defaultImportance;
      case NotificationPriority.low:
        return Importance.low;
    }
  }

  Priority _getPriority(NotificationPriority priority) {
    switch (priority) {
      case NotificationPriority.critical:
        return Priority.max;
      case NotificationPriority.high:
        return Priority.high;
      case NotificationPriority.normal:
        return Priority.defaultPriority;
      case NotificationPriority.low:
        return Priority.low;
    }
  }

  // ============== Settings Management ==============

  /// Load settings from storage
  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    _settings = NotificationSettings(
      enabled: prefs.getBool('notif_enabled') ?? true,
      shiftNotifications: prefs.getBool('notif_shifts') ?? true,
      leaveNotifications: prefs.getBool('notif_leave') ?? true,
      scheduleNotifications: prefs.getBool('notif_schedule') ?? true,
      reminderNotifications: prefs.getBool('notif_reminders') ?? true,
      announcementNotifications: prefs.getBool('notif_announcements') ?? true,
      quietHoursEnabled: prefs.getBool('notif_quiet_hours') ?? false,
      quietHoursStart: TimeOfDay(
        hour: prefs.getInt('notif_quiet_start_hour') ?? 22,
        minute: prefs.getInt('notif_quiet_start_minute') ?? 0,
      ),
      quietHoursEnd: TimeOfDay(
        hour: prefs.getInt('notif_quiet_end_hour') ?? 7,
        minute: prefs.getInt('notif_quiet_end_minute') ?? 0,
      ),
      doNotDisturb: prefs.getBool('notif_dnd') ?? false,
    );
  }

  /// Save settings
  Future<void> updateSettings(NotificationSettings settings) async {
    _settings = settings;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('notif_enabled', settings.enabled);
    await prefs.setBool('notif_shifts', settings.shiftNotifications);
    await prefs.setBool('notif_leave', settings.leaveNotifications);
    await prefs.setBool('notif_schedule', settings.scheduleNotifications);
    await prefs.setBool('notif_reminders', settings.reminderNotifications);
    await prefs.setBool('notif_announcements', settings.announcementNotifications);
    await prefs.setBool('notif_quiet_hours', settings.quietHoursEnabled);
    await prefs.setInt('notif_quiet_start_hour', settings.quietHoursStart.hour);
    await prefs.setInt('notif_quiet_start_minute', settings.quietHoursStart.minute);
    await prefs.setInt('notif_quiet_end_hour', settings.quietHoursEnd.hour);
    await prefs.setInt('notif_quiet_end_minute', settings.quietHoursEnd.minute);
    await prefs.setBool('notif_dnd', settings.doNotDisturb);
  }

  /// Get current settings
  NotificationSettings getSettings() => _settings;

  /// Get FCM token
  Future<String?> getToken() async {
    return await _firebaseMessaging?.getToken();
  }

  /// Dispose resources
  void dispose() {
    _batchTimer?.cancel();
    _notificationController.close();
  }
}

// ============== Data Classes ==============

/// Notification payload
class NotificationPayload {
  final String id;
  final String title;
  final String body;
  final NotificationType type;
  final NotificationPriority priority;
  final Map<String, dynamic>? data;
  final DateTime? timestamp;

  NotificationPayload({
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    this.priority = NotificationPriority.normal,
    this.data,
    this.timestamp,
  });

  factory NotificationPayload.fromRemoteMessage(RemoteMessage message) {
    final notification = message.notification;
    final data = message.data;
    
    return NotificationPayload(
      id: message.messageId ?? DateTime.now().millisecondsSinceEpoch.toString(),
      title: notification?.title ?? data['title'] ?? 'Notification',
      body: notification?.body ?? data['body'] ?? '',
      type: NotificationType.values.firstWhere(
        (t) => t.name == data['type'],
        orElse: () => NotificationType.system,
      ),
      priority: NotificationPriority.values.firstWhere(
        (p) => p.name == data['priority'],
        orElse: () => NotificationPriority.normal,
      ),
      data: data,
      timestamp: message.sentTime ?? DateTime.now(),
    );
  }

  factory NotificationPayload.fromJson(Map<String, dynamic> json) {
    return NotificationPayload(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      body: json['body'] ?? '',
      type: NotificationType.values.firstWhere(
        (t) => t.name == json['type'],
        orElse: () => NotificationType.system,
      ),
      priority: NotificationPriority.values.firstWhere(
        (p) => p.name == json['priority'],
        orElse: () => NotificationPriority.normal,
      ),
      data: json['data'],
      timestamp: json['timestamp'] != null 
          ? DateTime.parse(json['timestamp']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'body': body,
    'type': type.name,
    'priority': priority.name,
    'data': data,
    'timestamp': timestamp?.toIso8601String(),
  };
}

/// Notification types
enum NotificationType {
  shiftAssigned,
  shiftUpdated,
  shiftCancelled,
  leaveApproved,
  leaveRejected,
  leaveReminder,
  schedulePublished,
  scheduleChange,
  reminder,
  announcement,
  system,
}

/// Notification priority levels
enum NotificationPriority {
  critical, // Always show, bypass DND
  high,     // Important, show prominently
  normal,   // Standard notification
  low,      // Can be batched, less intrusive
}

/// Notification settings
class NotificationSettings {
  final bool enabled;
  final bool shiftNotifications;
  final bool leaveNotifications;
  final bool scheduleNotifications;
  final bool reminderNotifications;
  final bool announcementNotifications;
  final bool quietHoursEnabled;
  final TimeOfDay quietHoursStart;
  final TimeOfDay quietHoursEnd;
  final bool doNotDisturb;

  NotificationSettings({
    this.enabled = true,
    this.shiftNotifications = true,
    this.leaveNotifications = true,
    this.scheduleNotifications = true,
    this.reminderNotifications = true,
    this.announcementNotifications = true,
    this.quietHoursEnabled = false,
    this.quietHoursStart = const TimeOfDay(hour: 22, minute: 0),
    this.quietHoursEnd = const TimeOfDay(hour: 7, minute: 0),
    this.doNotDisturb = false,
  });

  NotificationSettings copyWith({
    bool? enabled,
    bool? shiftNotifications,
    bool? leaveNotifications,
    bool? scheduleNotifications,
    bool? reminderNotifications,
    bool? announcementNotifications,
    bool? quietHoursEnabled,
    TimeOfDay? quietHoursStart,
    TimeOfDay? quietHoursEnd,
    bool? doNotDisturb,
  }) {
    return NotificationSettings(
      enabled: enabled ?? this.enabled,
      shiftNotifications: shiftNotifications ?? this.shiftNotifications,
      leaveNotifications: leaveNotifications ?? this.leaveNotifications,
      scheduleNotifications: scheduleNotifications ?? this.scheduleNotifications,
      reminderNotifications: reminderNotifications ?? this.reminderNotifications,
      announcementNotifications: announcementNotifications ?? this.announcementNotifications,
      quietHoursEnabled: quietHoursEnabled ?? this.quietHoursEnabled,
      quietHoursStart: quietHoursStart ?? this.quietHoursStart,
      quietHoursEnd: quietHoursEnd ?? this.quietHoursEnd,
      doNotDisturb: doNotDisturb ?? this.doNotDisturb,
    );
  }
}
