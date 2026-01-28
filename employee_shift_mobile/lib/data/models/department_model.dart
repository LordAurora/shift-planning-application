/// Departman modeli
class Department {
  final int id;
  final String name;
  final String? description;
  final String? location;
  final int? managerId;
  final String? managerName;
  final DateTime createdAt;
  final DateTime updatedAt;

  Department({
    required this.id,
    required this.name,
    this.description,
    this.location,
    this.managerId,
    this.managerName,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Department.fromJson(Map<String, dynamic> json) {
    return Department(
      id: json['id'] as int,
      name: json['name'] as String,
      description: json['description'] as String?,
      location: json['location'] as String?,
      managerId: json['manager_id'] as int?,
      managerName: json['manager_name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'location': location,
      'manager_id': managerId,
      'manager_name': managerName,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  @override
  String toString() => 'Department(id: $id, name: $name)';
}
