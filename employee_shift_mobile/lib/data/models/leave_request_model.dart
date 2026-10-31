/// İzin durumu enum'u
enum LeaveStatus {
  pending('pending'),
  approved('approved'),
  rejected('rejected');

  const LeaveStatus(this.value);
  final String value;

  static LeaveStatus fromString(String value) {
    return LeaveStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => LeaveStatus.pending,
    );
  }

  String get displayName {
    switch (this) {
      case LeaveStatus.pending:
        return 'Pending';
      case LeaveStatus.approved:
        return 'Approved';
      case LeaveStatus.rejected:
        return 'Rejected';
    }
  }
}

/// İzin tipi enum'u
enum LeaveType {
  annual('annual'),
  sick('sick'),
  personal('personal'),
  maternity('maternity'),
  unpaid('unpaid');

  const LeaveType(this.value);
  final String value;

  static LeaveType fromString(String value) {
    return LeaveType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => LeaveType.annual,
    );
  }

  String get displayName {
    switch (this) {
      case LeaveType.annual:
        return 'Annual leave';
      case LeaveType.sick:
        return 'Sick leave';
      case LeaveType.personal:
        return 'Personal leave';
      case LeaveType.maternity:
        return 'Maternity leave';
      case LeaveType.unpaid:
        return 'Unpaid leave';
    }
  }
}

/// İzin talebi modeli
class LeaveRequest {
  final int id;
  final int employeeId;
  final String? employeeName;
  final LeaveType type;
  final DateTime startDate;
  final DateTime endDate;
  final String? reason;
  final LeaveStatus status;
  final String? responseNote;
  final int? respondedBy;
  final String? responderName;
  final DateTime? respondedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  LeaveRequest({
    required this.id,
    required this.employeeId,
    this.employeeName,
    required this.type,
    required this.startDate,
    required this.endDate,
    this.reason,
    required this.status,
    this.responseNote,
    this.respondedBy,
    this.responderName,
    this.respondedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory LeaveRequest.fromJson(Map<String, dynamic> json) {
    return LeaveRequest(
      id: json['id'] as int,
      employeeId: json['employee_id'] as int,
      employeeName: json['employee_name'] as String?,
      type: LeaveType.fromString(json['type'] as String),
      startDate: DateTime.parse(json['start_date'] as String),
      endDate: DateTime.parse(json['end_date'] as String),
      reason: json['reason'] as String?,
      status: LeaveStatus.fromString(json['status'] as String),
      responseNote: json['response_note'] as String?,
      respondedBy: json['responded_by'] as int?,
      responderName: json['responder_name'] as String?,
      respondedAt: json['responded_at'] != null 
          ? DateTime.parse(json['responded_at'] as String) 
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'employee_id': employeeId,
      'employee_name': employeeName,
      'type': type.value,
      'start_date': startDate.toIso8601String(),
      'end_date': endDate.toIso8601String(),
      'reason': reason,
      'status': status.value,
      'response_note': responseNote,
      'responded_by': respondedBy,
      'responder_name': responderName,
      'responded_at': respondedAt?.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// İzin gün sayısını hesaplar
  int get totalDays {
    return endDate.difference(startDate).inDays + 1;
  }

  /// Beklemede mi?
  bool get isPending => status == LeaveStatus.pending;

  /// Onaylandı mı?
  bool get isApproved => status == LeaveStatus.approved;

  /// Reddedildi mi?
  bool get isRejected => status == LeaveStatus.rejected;

  LeaveRequest copyWith({
    int? id,
    int? employeeId,
    String? employeeName,
    LeaveType? type,
    DateTime? startDate,
    DateTime? endDate,
    String? reason,
    LeaveStatus? status,
    String? responseNote,
    int? respondedBy,
    String? responderName,
    DateTime? respondedAt,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return LeaveRequest(
      id: id ?? this.id,
      employeeId: employeeId ?? this.employeeId,
      employeeName: employeeName ?? this.employeeName,
      type: type ?? this.type,
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      reason: reason ?? this.reason,
      status: status ?? this.status,
      responseNote: responseNote ?? this.responseNote,
      respondedBy: respondedBy ?? this.respondedBy,
      responderName: responderName ?? this.responderName,
      respondedAt: respondedAt ?? this.respondedAt,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() => 'LeaveRequest(id: $id, type: ${type.value}, status: ${status.value})';
}

/// İzin talebi oluşturma
class CreateLeaveRequest {
  final LeaveType type;
  final DateTime startDate;
  final DateTime endDate;
  final String? reason;

  CreateLeaveRequest({
    required this.type,
    required this.startDate,
    required this.endDate,
    this.reason,
  });

  Map<String, dynamic> toJson() {
    return {
      'type': type.value,
      'start_date': startDate.toIso8601String().split('T')[0],
      'end_date': endDate.toIso8601String().split('T')[0],
      'reason': reason,
    };
  }
}
