import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

import 'local_database_service.dart';
import 'api/api_client.dart';

/// Synchronization service for offline-first data management.
/// Handles background sync, conflict resolution, and data freshness.
class SyncService {
  final LocalDatabaseService _localDb;
  final ApiClient _apiClient;
  final Connectivity _connectivity = Connectivity();
  
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;
  Timer? _syncTimer;
  bool _isSyncing = false;
  
  // Sync configuration
  static const Duration _syncInterval = Duration(minutes: 5);
  static const int _maxRetries = 5;
  
  // Stream controllers for sync status
  final _syncStatusController = StreamController<SyncStatus>.broadcast();
  Stream<SyncStatus> get syncStatus => _syncStatusController.stream;
  
  SyncService({
    required LocalDatabaseService localDb,
    required ApiClient apiClient,
  })  : _localDb = localDb,
        _apiClient = apiClient;

  /// Initialize sync service
  Future<void> initialize() async {
    // Listen for connectivity changes
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      _onConnectivityChanged,
    );
    
    // Start periodic sync
    _syncTimer = Timer.periodic(_syncInterval, (_) => syncAll());
    
    // Initial sync if online
    final connectivityList = await _connectivity.checkConnectivity();
    if (_hasConnection(connectivityList)) {
      syncAll();
    }
  }

  /// Check if any connectivity result indicates connection
  bool _hasConnection(List<ConnectivityResult> results) {
    return results.isNotEmpty && 
           !results.every((r) => r == ConnectivityResult.none);
  }

  /// Handle connectivity changes
  void _onConnectivityChanged(List<ConnectivityResult> results) {
    if (_hasConnection(results)) {
      // Back online - trigger sync
      debugPrint('Connectivity restored, triggering sync...');
      syncAll();
    } else {
      debugPrint('Offline mode activated');
      _syncStatusController.add(SyncStatus(
        status: SyncState.offline,
        message: 'Working offline',
      ));
    }
  }

  /// Perform full sync
  Future<SyncResult> syncAll() async {
    if (_isSyncing) {
      return SyncResult(success: false, message: 'Sync already in progress');
    }

    _isSyncing = true;
    _syncStatusController.add(SyncStatus(
      status: SyncState.syncing,
      message: 'Syncing...',
    ));

    try {
      // Check connectivity first
      final connectivityList = await _connectivity.checkConnectivity();
      if (!_hasConnection(connectivityList)) {
        _syncStatusController.add(SyncStatus(
          status: SyncState.offline,
          message: 'No internet connection',
        ));
        return SyncResult(success: false, message: 'No internet connection');
      }

      // 1. Process pending sync queue (uploads first)
      await _processSyncQueue();

      // 2. Fetch and cache fresh data from server
      await _fetchAndCacheData();

      // 3. Check for conflicts
      await _resolveConflicts();

      _syncStatusController.add(SyncStatus(
        status: SyncState.synced,
        message: 'Up to date',
        lastSyncTime: DateTime.now(),
      ));

      return SyncResult(success: true, message: 'Sync completed');
    } catch (e) {
      debugPrint('Sync failed: $e');
      _syncStatusController.add(SyncStatus(
        status: SyncState.error,
        message: 'Sync failed: ${e.toString()}',
      ));
      return SyncResult(success: false, message: e.toString());
    } finally {
      _isSyncing = false;
    }
  }

  /// Process pending sync queue
  Future<void> _processSyncQueue() async {
    final pendingOps = await _localDb.getPendingSyncOperations();
    final failedOps = await _localDb.getFailedSyncOperations();
    
    final allOps = [...pendingOps, ...failedOps];
    
    for (final op in allOps) {
      try {
        final payload = jsonDecode(op['payload'] as String);
        final operation = op['operation'] as String;
        final entityType = op['entity_type'] as String;
        final entityId = op['entity_id'] as int?;
        
        switch ('$operation:$entityType') {
          case 'CREATE:leave_request':
            await _syncCreateLeaveRequest(payload);
            break;
          case 'UPDATE:shift':
            await _syncUpdateShift(entityId!, payload);
            break;
          case 'UPDATE:notification':
            await _syncUpdateNotification(entityId!, payload);
            break;
          // Add more operation handlers as needed
        }
        
        // Mark as completed
        await _localDb.markSyncCompleted(op['id'] as int);
        
      } catch (e) {
        debugPrint('Sync operation failed: $e');
        await _localDb.markSyncFailed(op['id'] as int, e.toString());
      }
    }
  }

  /// Sync create leave request
  Future<void> _syncCreateLeaveRequest(Map<String, dynamic> payload) async {
    await _apiClient.post('/leave-requests', data: payload);
  }

  /// Sync update shift
  Future<void> _syncUpdateShift(int shiftId, Map<String, dynamic> payload) async {
    await _apiClient.put('/shifts/$shiftId', data: payload);
  }

  /// Sync update notification
  Future<void> _syncUpdateNotification(int notifId, Map<String, dynamic> payload) async {
    if (payload['is_read'] == true) {
      await _apiClient.put('/notifications/$notifId/read', data: {});
    }
  }

  /// Fetch and cache fresh data from server
  Future<void> _fetchAndCacheData() async {
    try {
      // Fetch shifts
      final shiftsResponse = await _apiClient.get('/shifts/my');
      final shiftsData = shiftsResponse.data;
      if (shiftsData != null && shiftsData['items'] != null) {
        await _localDb.cacheShifts(List<Map<String, dynamic>>.from(shiftsData['items']));
      }
      
      // Fetch leave requests
      final leaveResponse = await _apiClient.get('/leave-requests/my');
      final leaveData = leaveResponse.data;
      if (leaveData != null && leaveData['items'] != null) {
        await _localDb.cacheLeaveRequests(List<Map<String, dynamic>>.from(leaveData['items']));
      }
      
      // Fetch notifications
      final notifResponse = await _apiClient.get('/notifications');
      final notifData = notifResponse.data;
      if (notifData != null && notifData['items'] != null) {
        await _localDb.cacheNotifications(List<Map<String, dynamic>>.from(notifData['items']));
      }
      
    } catch (e) {
      debugPrint('Failed to fetch fresh data: $e');
      // Don't throw - partial sync is OK
    }
  }

  /// Resolve any data conflicts
  Future<void> _resolveConflicts() async {
    // Get shifts with conflicts
    final conflictedShifts = await _localDb.getCachedShifts();
    
    for (final shift in conflictedShifts) {
      if (shift['sync_conflict'] == 1) {
        // Apply conflict resolution strategy
        // Default: Server wins (last-write-wins with server priority)
        await _resolveShiftConflict(shift);
      }
    }
  }

  /// Resolve individual shift conflict
  Future<void> _resolveShiftConflict(Map<String, dynamic> localShift) async {
    final serverId = localShift['server_id'];
    if (serverId == null) return;
    
    try {
      // Fetch server version
      final response = await _apiClient.get('/shifts/$serverId');
      final serverShift = response.data as Map<String, dynamic>?;
      if (serverShift == null) return;
      
      final serverUpdatedAt = DateTime.parse(serverShift['updated_at'] ?? '');
      final localUpdatedAt = DateTime.parse(localShift['local_modified_at'] ?? '');
      
      if (serverUpdatedAt.isAfter(localUpdatedAt)) {
        // Server wins - update local
        await _localDb.cacheShifts([serverShift]);
      } else {
        // Local wins - push to server
        await _apiClient.put('/shifts/$serverId', data: localShift);
      }
      
      // Clear conflict flag
      // Would need to add a method for this
      
    } catch (e) {
      debugPrint('Failed to resolve conflict for shift $serverId: $e');
    }
  }

  /// Sync specific entity type
  Future<void> syncEntity(String entityType) async {
    switch (entityType) {
      case 'shifts':
        final response = await _apiClient.get('/shifts/my');
        final data = response.data;
        if (data != null && data['items'] != null) {
          await _localDb.cacheShifts(List<Map<String, dynamic>>.from(data['items']));
        }
        break;
      case 'leave_requests':
        final response = await _apiClient.get('/leave-requests/my');
        final data = response.data;
        if (data != null && data['items'] != null) {
          await _localDb.cacheLeaveRequests(List<Map<String, dynamic>>.from(data['items']));
        }
        break;
      case 'notifications':
        final response = await _apiClient.get('/notifications');
        final data = response.data;
        if (data != null && data['items'] != null) {
          await _localDb.cacheNotifications(List<Map<String, dynamic>>.from(data['items']));
        }
        break;
    }
  }

  /// Get current sync status
  Future<Map<String, dynamic>> getStatus() async {
    return await _localDb.getSyncStatus();
  }

  /// Force immediate sync
  Future<SyncResult> forceSync() async {
    return await syncAll();
  }

  /// Cleanup resources
  void dispose() {
    _connectivitySubscription?.cancel();
    _syncTimer?.cancel();
    _syncStatusController.close();
  }
}

/// Sync status update
class SyncStatus {
  final SyncState status;
  final String message;
  final DateTime? lastSyncTime;
  final int? pendingCount;
  final int? failedCount;

  SyncStatus({
    required this.status,
    required this.message,
    this.lastSyncTime,
    this.pendingCount,
    this.failedCount,
  });
}

/// Sync states
enum SyncState {
  synced,
  syncing,
  offline,
  error,
  pending,
}

/// Sync operation result
class SyncResult {
  final bool success;
  final String message;
  final int? syncedCount;
  final int? failedCount;
  final List<String>? errors;

  SyncResult({
    required this.success,
    required this.message,
    this.syncedCount,
    this.failedCount,
    this.errors,
  });
}
