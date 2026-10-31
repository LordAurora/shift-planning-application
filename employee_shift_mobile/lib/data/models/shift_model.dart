/// Vardiya durumu enum'u - Backend ile uyumlu
enum ShiftStatus {
  scheduled('scheduled'),
  completed('completed'),
  cancelled('cancelled');

  const ShiftStatus(this.value);
  final String value;

  static ShiftStatus fromString(String value) {
    return ShiftStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ShiftStatus.scheduled,
    );
  }

  String get displayName {
    switch (this) {
      case ShiftStatus.scheduled:
        return 'Scheduled';
      case ShiftStatus.completed:
        return 'Completed';
      case ShiftStatus.cancelled:
        return 'Cancelled';
    }
  }
}

/// Vardiya modeli
class Shift {
  final int id;
  final int employeeId;
  final String? employeeName;
  final int departmentId;
  final String? departmentName;
  final DateTime startTime;
  final DateTime endTime;
  final ShiftStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;

  Shift({
    required this.id,
    required this.employeeId,
    this.employeeName,
    required this.departmentId,
    this.departmentName,
    required this.startTime,
    required this.endTime,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Shift.fromJson(Map<String, dynamic> json) {
    return Shift(
      id: json['id'] as int,
      employeeId: json['employee_id'] as int,
      employeeName: json['employee_name'] as String?,
      departmentId: json['department_id'] as int,
      departmentName: json['department_name'] as String?,
      startTime: DateTime.parse(json['start_time'] as String),
      endTime: DateTime.parse(json['end_time'] as String),
      status: ShiftStatus.fromString(json['status'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'employee_id': employeeId,
      'employee_name': employeeName,
      'department_id': departmentId,
      'department_name': departmentName,
      'start_time': startTime.toIso8601String(),
      'end_time': endTime.toIso8601String(),
      'status': status.value,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// Vardiya süresini saat cinsinden döndürür
  double get durationHours {
    return endTime.difference(startTime).inMinutes / 60;
  }

  /// Vardiya süresini formatlanmış string olarak döndürür
  String get formattedDuration {
    final duration = endTime.difference(startTime);
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    if (minutes == 0) {
      return '${hours}h';
    }
    return '${hours}h ${minutes}m';
  }

  /// Bugünkü vardiya mı?
  bool get isToday {
    final now = DateTime.now();
    return startTime.year == now.year &&
        startTime.month == now.month &&
        startTime.day == now.day;
  }

  /// Şu an aktif mi?
  bool get isActive {
    final now = DateTime.now();
    return now.isAfter(startTime) && now.isBefore(endTime) && status == ShiftStatus.scheduled;
  }

  /// Yaklaşan vardiya mı? (Henüz başlamamış)
  bool get isUpcoming {
    return startTime.isAfter(DateTime.now()) && status == ShiftStatus.scheduled;
  }

  /// Geçmiş vardiya mı?
  bool get isPast {
    return endTime.isBefore(DateTime.now());
  }

  Shift copyWith({
    int? id,
    int? employeeId,
    String? employeeName,
    int? departmentId,
    String? departmentName,
    DateTime? startTime,
    DateTime? endTime,
    ShiftStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Shift(
      id: id ?? this.id,
      employeeId: employeeId ?? this.employeeId,
      employeeName: employeeName ?? this.employeeName,
      departmentId: departmentId ?? this.departmentId,
      departmentName: departmentName ?? this.departmentName,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() => 'Shift(id: $id, date: ${startTime.toString()}, status: ${status.value})';
}

/// Vardiya listesi yanıtı
class ShiftListResponse {
  final List<Shift> items;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;

  ShiftListResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.totalPages,
  });

  factory ShiftListResponse.fromJson(Map<String, dynamic> json) {
    return ShiftListResponse(
      items: (json['items'] as List<dynamic>)
          .map((item) => Shift.fromJson(item as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
      totalPages: json['total_pages'] as int,
    );
  }
}
