import 'dart:async';
import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:flutter/foundation.dart';

/// Local database service for offline-first support.
/// Handles caching, sync queues, and conflict resolution.
class LocalDatabaseService {
  static Database? _database;
  static const String _dbName = 'shiftmaster_local.db';
  static const int _dbVersion = 1;

  /// Get database instance
  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  /// Initialize database
  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _dbName);

    return await openDatabase(
      path,
      version: _dbVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  /// Create database tables
  Future<void> _onCreate(Database db, int version) async {
    // Shifts cache table
    await db.execute('''
      CREATE TABLE shifts (
        id INTEGER PRIMARY KEY,
        server_id INTEGER UNIQUE,
        title TEXT NOT NULL,
        description TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        department_id INTEGER,
        department_name TEXT,
        status TEXT DEFAULT 'assigned',
        employee_id INTEGER,
        employee_name TEXT,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT,
        is_synced INTEGER DEFAULT 1,
        local_modified_at TEXT,
        sync_conflict INTEGER DEFAULT 0
      )
    ''');

    // Leave requests cache
    await db.execute('''
      CREATE TABLE leave_requests (
        id INTEGER PRIMARY KEY,
        server_id INTEGER UNIQUE,
        leave_type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        updated_at TEXT,
        is_synced INTEGER DEFAULT 1,
        local_modified_at TEXT
      )
    ''');

    // Notifications cache
    await db.execute('''
      CREATE TABLE notifications (
        id INTEGER PRIMARY KEY,
        server_id INTEGER UNIQUE,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TEXT,
        data TEXT
      )
    ''');

    // Sync queue for offline operations
    await db.execute('''
      CREATE TABLE sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL,
        retry_count INTEGER DEFAULT 0,
        last_error TEXT,
        status TEXT DEFAULT 'pending'
      )
    ''');

    // User preferences
    await db.execute('''
      CREATE TABLE user_preferences (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT
      )
    ''');

    // Create indexes
    await db.execute('CREATE INDEX idx_shifts_date ON shifts(start_time)');
    await db.execute('CREATE INDEX idx_shifts_synced ON shifts(is_synced)');
    await db.execute('CREATE INDEX idx_sync_queue_status ON sync_queue(status)');
    await db.execute('CREATE INDEX idx_leave_requests_date ON leave_requests(start_date)');
  }

  /// Handle database upgrades
  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Add migration logic here for future versions
    if (oldVersion < 2) {
      // Example migration for version 2
    }
  }

  // ============== Shift Operations ==============

  /// Cache shifts from server
  Future<void> cacheShifts(List<Map<String, dynamic>> shifts) async {
    final db = await database;
    final batch = db.batch();

    for (final shift in shifts) {
      batch.insert(
        'shifts',
        {
          'server_id': shift['id'],
          'title': shift['title'],
          'description': shift['description'],
          'start_time': shift['start_time'],
          'end_time': shift['end_time'],
          'department_id': shift['department_id'],
          'department_name': shift['department']?['name'],
          'status': shift['status'] ?? 'assigned',
          'employee_id': shift['employee_id'],
          'employee_name': shift['employee']?['name'],
          'notes': shift['notes'],
          'created_at': shift['created_at'],
          'updated_at': shift['updated_at'],
          'is_synced': 1,
          'local_modified_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
  }

  /// Get cached shifts
  Future<List<Map<String, dynamic>>> getCachedShifts({
    DateTime? startDate,
    DateTime? endDate,
    bool onlyUnsynced = false,
  }) async {
    final db = await database;
    
    String whereClause = '';
    List<dynamic> whereArgs = [];

    if (startDate != null) {
      whereClause += 'start_time >= ?';
      whereArgs.add(startDate.toIso8601String());
    }

    if (endDate != null) {
      if (whereClause.isNotEmpty) whereClause += ' AND ';
      whereClause += 'end_time <= ?';
      whereArgs.add(endDate.toIso8601String());
    }

    if (onlyUnsynced) {
      if (whereClause.isNotEmpty) whereClause += ' AND ';
      whereClause += 'is_synced = 0';
    }

    return await db.query(
      'shifts',
      where: whereClause.isNotEmpty ? whereClause : null,
      whereArgs: whereArgs.isNotEmpty ? whereArgs : null,
      orderBy: 'start_time ASC',
    );
  }

  /// Mark shift as modified locally
  Future<void> markShiftModified(int localId) async {
    final db = await database;
    await db.update(
      'shifts',
      {
        'is_synced': 0,
        'local_modified_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [localId],
    );
  }

  // ============== Leave Request Operations ==============

  /// Cache leave requests
  Future<void> cacheLeaveRequests(List<Map<String, dynamic>> requests) async {
    final db = await database;
    final batch = db.batch();

    for (final request in requests) {
      batch.insert(
        'leave_requests',
        {
          'server_id': request['id'],
          'leave_type': request['leave_type'],
          'start_date': request['start_date'],
          'end_date': request['end_date'],
          'reason': request['reason'],
          'status': request['status'],
          'created_at': request['created_at'],
          'updated_at': request['updated_at'],
          'is_synced': 1,
          'local_modified_at': DateTime.now().toIso8601String(),
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
  }

  /// Get cached leave requests
  Future<List<Map<String, dynamic>>> getCachedLeaveRequests() async {
    final db = await database;
    return await db.query(
      'leave_requests',
      orderBy: 'start_date DESC',
    );
  }

  /// Create leave request locally (for offline)
  Future<int> createLocalLeaveRequest(Map<String, dynamic> request) async {
    final db = await database;
    
    final id = await db.insert('leave_requests', {
      ...request,
      'is_synced': 0,
      'status': 'pending_sync',
      'local_modified_at': DateTime.now().toIso8601String(),
    });

    // Add to sync queue
    await addToSyncQueue(
      operation: 'CREATE',
      entityType: 'leave_request',
      entityId: id,
      payload: request,
    );

    return id;
  }

  // ============== Sync Queue Operations ==============

  /// Add operation to sync queue
  Future<void> addToSyncQueue({
    required String operation,
    required String entityType,
    int? entityId,
    required Map<String, dynamic> payload,
  }) async {
    final db = await database;
    await db.insert('sync_queue', {
      'operation': operation,
      'entity_type': entityType,
      'entity_id': entityId,
      'payload': jsonEncode(payload),
      'created_at': DateTime.now().toIso8601String(),
      'status': 'pending',
    });
  }

  /// Get pending sync operations
  Future<List<Map<String, dynamic>>> getPendingSyncOperations() async {
    final db = await database;
    return await db.query(
      'sync_queue',
      where: 'status = ?',
      whereArgs: ['pending'],
      orderBy: 'created_at ASC',
    );
  }

  /// Mark sync operation as completed
  Future<void> markSyncCompleted(int queueId) async {
    final db = await database;
    await db.delete(
      'sync_queue',
      where: 'id = ?',
      whereArgs: [queueId],
    );
  }

  /// Mark sync operation as failed
  Future<void> markSyncFailed(int queueId, String error) async {
    final db = await database;
    await db.update(
      'sync_queue',
      {
        'retry_count': Sqflite.firstIntValue(await db.rawQuery(
          'SELECT retry_count FROM sync_queue WHERE id = ?',
          [queueId],
        ))! + 1,
        'last_error': error,
        'status': 'retry',
      },
      where: 'id = ?',
      whereArgs: [queueId],
    );
  }

  /// Get failed sync operations
  Future<List<Map<String, dynamic>>> getFailedSyncOperations() async {
    final db = await database;
    return await db.query(
      'sync_queue',
      where: 'status = ? AND retry_count < 5',
      whereArgs: ['retry'],
      orderBy: 'retry_count ASC, created_at ASC',
    );
  }

  // ============== Notification Operations ==============

  /// Cache notifications
  Future<void> cacheNotifications(List<Map<String, dynamic>> notifications) async {
    final db = await database;
    final batch = db.batch();

    for (final notif in notifications) {
      batch.insert(
        'notifications',
        {
          'server_id': notif['id'],
          'title': notif['title'],
          'message': notif['message'],
          'type': notif['type'],
          'is_read': notif['is_read'] == true ? 1 : 0,
          'created_at': notif['created_at'],
          'data': notif['data'] != null ? jsonEncode(notif['data']) : null,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
  }

  /// Get cached notifications
  Future<List<Map<String, dynamic>>> getCachedNotifications({
    bool unreadOnly = false,
  }) async {
    final db = await database;
    return await db.query(
      'notifications',
      where: unreadOnly ? 'is_read = 0' : null,
      orderBy: 'created_at DESC',
    );
  }

  /// Mark notification as read locally
  Future<void> markNotificationRead(int serverId) async {
    final db = await database;
    await db.update(
      'notifications',
      {'is_read': 1},
      where: 'server_id = ?',
      whereArgs: [serverId],
    );
  }

  // ============== User Preferences ==============

  /// Save user preference
  Future<void> setPreference(String key, String value) async {
    final db = await database;
    await db.insert(
      'user_preferences',
      {
        'key': key,
        'value': value,
        'updated_at': DateTime.now().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Get user preference
  Future<String?> getPreference(String key) async {
    final db = await database;
    final result = await db.query(
      'user_preferences',
      where: 'key = ?',
      whereArgs: [key],
    );
    if (result.isNotEmpty) {
      return result.first['value'] as String?;
    }
    return null;
  }

  // ============== Utility Methods ==============

  /// Clear all cached data (for logout)
  Future<void> clearAllData() async {
    final db = await database;
    await db.delete('shifts');
    await db.delete('leave_requests');
    await db.delete('notifications');
    await db.delete('sync_queue');
    await db.delete('user_preferences');
  }

  /// Get sync status summary
  Future<Map<String, dynamic>> getSyncStatus() async {
    final db = await database;
    
    final pendingCount = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM sync_queue WHERE status = ?', ['pending']),
    ) ?? 0;
    
    final failedCount = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM sync_queue WHERE status = ?', ['retry']),
    ) ?? 0;
    
    final unsyncedShifts = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM shifts WHERE is_synced = 0'),
    ) ?? 0;
    
    final unsyncedLeaveRequests = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM leave_requests WHERE is_synced = 0'),
    ) ?? 0;

    return {
      'pending_operations': pendingCount,
      'failed_operations': failedCount,
      'unsynced_shifts': unsyncedShifts,
      'unsynced_leave_requests': unsyncedLeaveRequests,
      'total_unsynced': pendingCount + failedCount + unsyncedShifts + unsyncedLeaveRequests,
    };
  }

  /// Close database
  Future<void> close() async {
    if (_database != null) {
      await _database!.close();
      _database = null;
    }
  }
}
