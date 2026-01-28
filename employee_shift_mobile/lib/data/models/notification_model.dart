/// Bildirim tipi enum'u - Backend ile uyumlu
enum NotificationType {
  info('info'),
  warning('warning'),
  error('error'),
  success('success');

  const NotificationType(this.value);
  final String value;

  static NotificationType fromString(String value) {
    return NotificationType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => NotificationType.info,
    );
  }
}

/// Bildirim kategorisi - Deep link için
enum NotificationCategory {
  shiftChange('shift_change'),
  locationChange('location_change'),
  emergencyCall('emergency_call'),
  announcement('announcement'),
  leaveResult('leave_result'),
  general('general');

  const NotificationCategory(this.value);
  final String value;

  static NotificationCategory fromString(String value) {
    return NotificationCategory.values.firstWhere(
      (cat) => cat.value == value,
      orElse: () => NotificationCategory.general,
    );
  }
}

/// Bildirim modeli
class AppNotification {
  final int id;
  final int userId;
  final String title;
  final String message;
  final NotificationType type;
  final NotificationCategory category;
  final bool isRead;
  final Map<String, dynamic>? data; // Ek veri (shift_id, leave_id vs.)
  final DateTime createdAt;

  AppNotification({
    required this.id,
    required this.userId,
    required this.title,
    required this.message,
    required this.type,
    this.category = NotificationCategory.general,
    required this.isRead,
    this.data,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      title: json['title'] as String,
      message: json['message'] as String,
      type: NotificationType.fromString(json['type'] as String),
      category: NotificationCategory.fromString(json['category'] as String? ?? 'general'),
      isRead: json['is_read'] as bool? ?? false,
      data: json['data'] as Map<String, dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'title': title,
      'message': message,
      'type': type.value,
      'category': category.value,
      'is_read': isRead,
      'data': data,
      'created_at': createdAt.toIso8601String(),
    };
  }

  /// Bildirimin göreceli zamanını döndürür
  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(createdAt);

    if (difference.inDays > 7) {
      return '${createdAt.day}.${createdAt.month}.${createdAt.year}';
    } else if (difference.inDays > 0) {
      return '${difference.inDays} gün önce';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} saat önce';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} dakika önce';
    } else {
      return 'Şimdi';
    }
  }

  /// Deep link için hedef route'u döndürür
  String? get targetRoute {
    switch (category) {
      case NotificationCategory.shiftChange:
        return '/shifts/weekly';
      case NotificationCategory.emergencyCall:
        return '/home';
      case NotificationCategory.leaveResult:
        return '/leave-requests';
      case NotificationCategory.locationChange:
        return '/shifts/weekly';
      case NotificationCategory.announcement:
        return '/notifications';
      case NotificationCategory.general:
        return null;
    }
  }

  AppNotification copyWith({
    int? id,
    int? userId,
    String? title,
    String? message,
    NotificationType? type,
    NotificationCategory? category,
    bool? isRead,
    Map<String, dynamic>? data,
    DateTime? createdAt,
  }) {
    return AppNotification(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      title: title ?? this.title,
      message: message ?? this.message,
      type: type ?? this.type,
      category: category ?? this.category,
      isRead: isRead ?? this.isRead,
      data: data ?? this.data,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  String toString() => 'Notification(id: $id, title: $title, isRead: $isRead)';
}
