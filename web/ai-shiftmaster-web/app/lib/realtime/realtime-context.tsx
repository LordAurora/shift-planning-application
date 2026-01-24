'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';

/**
 * Real-time event types
 */
export type EventType =
  | 'shift:created'
  | 'shift:updated'
  | 'shift:deleted'
  | 'shift:assigned'
  | 'leave:requested'
  | 'leave:approved'
  | 'leave:rejected'
  | 'schedule:published'
  | 'notification:new'
  | 'employee:updated'
  | 'system:announcement';

/**
 * Real-time event payload
 */
export interface RealtimeEvent<T = unknown> {
  type: EventType;
  data: T;
  timestamp: string;
  userId?: number;
  correlationId?: string;
}

/**
 * Connection status
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * Real-time context interface
 */
interface RealtimeContextType {
  status: ConnectionStatus;
  lastEvent: RealtimeEvent | null;
  subscribe: <T>(eventType: EventType, callback: (data: T) => void) => () => void;
  unsubscribeAll: () => void;
  reconnect: () => void;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

/**
 * Real-time Provider using Server-Sent Events (SSE)
 * Falls back to polling if SSE is not supported
 */
export function RealtimeProvider({ 
  children,
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}: { 
  children: ReactNode;
  apiUrl?: string;
}) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [subscribers, setSubscribers] = useState<Map<EventType, Set<(data: unknown) => void>>>(
    new Map()
  );

  /**
   * Connect to SSE endpoint
   */
  const connect = useCallback(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setStatus('disconnected');
      return;
    }

    setStatus('connecting');

    try {
      // Create SSE connection
      const url = `${apiUrl}/api/v1/events/stream?token=${encodeURIComponent(token)}`;
      const es = new EventSource(url);

      es.onopen = () => {
        console.log('SSE connected');
        setStatus('connected');
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as RealtimeEvent;
          setLastEvent(data);
          
          // Notify subscribers
          const eventSubscribers = subscribers.get(data.type);
          if (eventSubscribers) {
            eventSubscribers.forEach((callback) => callback(data.data));
          }
        } catch (error) {
          console.error('Failed to parse SSE event:', error);
        }
      };

      es.onerror = (error) => {
        console.error('SSE error:', error);
        setStatus('error');
        es.close();
        
        // Attempt reconnection after 5 seconds
        setTimeout(() => {
          if (localStorage.getItem('auth_token')) {
            connect();
          }
        }, 5000);
      };

      setEventSource(es);
    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      setStatus('error');
      
      // Fall back to polling
      startPolling();
    }
  }, [apiUrl, subscribers]);

  /**
   * Fallback polling mechanism
   */
  const startPolling = useCallback(() => {
    const pollInterval = setInterval(async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        clearInterval(pollInterval);
        return;
      }

      try {
        const response = await fetch(`${apiUrl}/api/v1/events/poll`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const events = await response.json() as RealtimeEvent[];
          events.forEach((event) => {
            setLastEvent(event);
            const eventSubscribers = subscribers.get(event.type);
            if (eventSubscribers) {
              eventSubscribers.forEach((callback) => callback(event.data));
            }
          });
          setStatus('connected');
        }
      } catch (error) {
        console.error('Polling failed:', error);
        setStatus('error');
      }
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(pollInterval);
  }, [apiUrl, subscribers]);

  /**
   * Disconnect from SSE
   */
  const disconnect = useCallback(() => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    setStatus('disconnected');
  }, [eventSource]);

  /**
   * Subscribe to event type
   */
  const subscribe = useCallback(<T,>(
    eventType: EventType,
    callback: (data: T) => void
  ): (() => void) => {
    setSubscribers((prev) => {
      const newSubscribers = new Map(prev);
      const eventSubscribers = newSubscribers.get(eventType) || new Set();
      eventSubscribers.add(callback as (data: unknown) => void);
      newSubscribers.set(eventType, eventSubscribers);
      return newSubscribers;
    });

    // Return unsubscribe function
    return () => {
      setSubscribers((prev) => {
        const newSubscribers = new Map(prev);
        const eventSubscribers = newSubscribers.get(eventType);
        if (eventSubscribers) {
          eventSubscribers.delete(callback as (data: unknown) => void);
          if (eventSubscribers.size === 0) {
            newSubscribers.delete(eventType);
          }
        }
        return newSubscribers;
      });
    };
  }, []);

  /**
   * Unsubscribe from all events
   */
  const unsubscribeAll = useCallback(() => {
    setSubscribers(new Map());
  }, []);

  /**
   * Manual reconnection
   */
  const reconnect = useCallback(() => {
    disconnect();
    connect();
  }, [disconnect, connect]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  // Reconnect when auth changes
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'auth_token') {
        if (e.newValue) {
          connect();
        } else {
          disconnect();
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [connect, disconnect]);

  const value: RealtimeContextType = {
    status,
    lastEvent,
    subscribe,
    unsubscribeAll,
    reconnect,
  };

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  );
}

/**
 * Hook to use realtime context
 */
export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (context === undefined) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}

/**
 * Hook to subscribe to specific event types
 */
export function useRealtimeEvent<T>(
  eventType: EventType,
  callback: (data: T) => void,
  deps: React.DependencyList = []
) {
  const { subscribe } = useRealtime();

  useEffect(() => {
    const unsubscribe = subscribe<T>(eventType, callback);
    return unsubscribe;
  }, [eventType, ...deps]);
}

/**
 * Hook for shift updates
 */
export function useShiftUpdates(
  onUpdate: (shift: unknown) => void
) {
  useRealtimeEvent('shift:created', onUpdate);
  useRealtimeEvent('shift:updated', onUpdate);
  useRealtimeEvent('shift:deleted', onUpdate);
  useRealtimeEvent('shift:assigned', onUpdate);
}

/**
 * Hook for notification updates
 */
export function useNotificationUpdates(
  onNotification: (notification: unknown) => void
) {
  useRealtimeEvent('notification:new', onNotification);
}

/**
 * Hook for leave request updates
 */
export function useLeaveUpdates(
  onUpdate: (leave: unknown) => void
) {
  useRealtimeEvent('leave:requested', onUpdate);
  useRealtimeEvent('leave:approved', onUpdate);
  useRealtimeEvent('leave:rejected', onUpdate);
}

/**
 * Connection status indicator component
 */
export function ConnectionIndicator() {
  const { status, reconnect } = useRealtime();

  const statusColors = {
    connecting: 'bg-yellow-500',
    connected: 'bg-green-500',
    disconnected: 'bg-gray-500',
    error: 'bg-red-500',
  };

  const statusText = {
    connecting: 'Connecting...',
    connected: 'Live',
    disconnected: 'Offline',
    error: 'Connection Error',
  };

  return (
    <div className="flex items-center gap-2">
      <span
        className={`w-2 h-2 rounded-full ${statusColors[status]} ${
          status === 'connected' ? 'animate-pulse' : ''
        }`}
      />
      <span className="text-xs text-gray-500">{statusText[status]}</span>
      {status === 'error' && (
        <button
          onClick={reconnect}
          className="text-xs text-blue-500 hover:underline"
        >
          Retry
        </button>
      )}
    </div>
  );
}
