import {
  createContext,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
  useContext,
  type Accessor,
  type ParentProps,
} from "solid-js";
import { createStore } from "solid-js/store";
import { DayContext, Task, Event, Day, TaskStatus } from "@/types/api";
import { taskAPI } from "@/utils/api";
import { getWebSocketBaseUrl, getWebSocketProtocol } from "@/utils/config";

interface StreamingDataContextValue {
  // The main data - provides loading/error states
  dayContext: Accessor<DayContext | undefined>;
  tasks: Accessor<Task[]>;
  events: Accessor<Event[]>;
  day: Accessor<Day | undefined>;
  // Loading and error states
  isLoading: Accessor<boolean>;
  error: Accessor<Error | undefined>;
  // Connection state
  isConnected: Accessor<boolean>;
  isOutOfSync: Accessor<boolean>;
  // Actions
  sync: () => void;
  syncIncremental: (sinceTimestamp: string) => void;
  setTaskStatus: (task: Task, status: TaskStatus) => Promise<void>;
}

const StreamingDataContext = createContext<StreamingDataContextValue>();

// WebSocket message types
interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

interface SyncRequestMessage extends WebSocketMessage {
  type: "sync_request";
  since_timestamp?: string | null;
}

interface SyncResponseMessage extends WebSocketMessage {
  type: "sync_response";
  day_context?: DayContext;
  changes?: EntityChange[];
  last_audit_log_timestamp?: string | null;
}

interface AuditLogEventMessage extends WebSocketMessage {
  type: "audit_log_event";
  audit_log?: {
    id: string;
    user_id: string;
    activity_type: string;
    occurred_at: string;
    entity_id: string | null;
    entity_type: string | null;
    meta: Record<string, unknown>;
  };
}

interface ConnectionAckMessage extends WebSocketMessage {
  type: "connection_ack";
  user_id: string;
}

interface ErrorMessage extends WebSocketMessage {
  type: "error";
  code: string;
  message: string;
}

interface EntityChange {
  change_type: "created" | "updated" | "deleted";
  entity_type: string;
  entity_id: string;
  entity_data: Task | Event | null;
}

export function StreamingDataProvider(props: ParentProps) {
  const [dayContextStore, setDayContextStore] = createStore<{
    data: DayContext | undefined;
  }>({ data: undefined });
  const [isLoading, setIsLoading] = createSignal(true);
  const [error, setError] = createSignal<Error | undefined>(undefined);
  const [isConnected, setIsConnected] = createSignal(false);
  const [isOutOfSync, setIsOutOfSync] = createSignal(false);
  const [lastProcessedTimestamp, setLastProcessedTimestamp] = createSignal<
    string | null
  >(null);

  let ws: WebSocket | null = null;
  let reconnectTimeout: number | null = null;
  let syncDebounceTimeout: number | null = null;
  let isMounted = false;

  // Derived values from the store
  const dayContext = createMemo(() => dayContextStore.data);
  const tasks = createMemo(() => dayContextStore.data?.tasks ?? []);
  const events = createMemo(
    () =>
      dayContextStore.data?.calendar_entries ??
      dayContextStore.data?.events ??
      []
  );
  const day = createMemo(() => dayContextStore.data?.day);

  // Get auth token from cookie
  const getCookie = (name: string): string | null => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
    return null;
  };

  // Connect to WebSocket
  const connectWebSocket = () => {
    setIsConnected(false);
    setError(undefined);

    const protocol = getWebSocketProtocol();
    const baseUrl = getWebSocketBaseUrl();
    const token = getCookie("lykke_auth");

    // Build WebSocket URL
    let wsUrl = `${protocol}//${baseUrl}/days/today/context`;
    if (token) {
      wsUrl += `?token=${encodeURIComponent(token)}`;
    }

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setError(undefined);
        console.log("StreamingDataProvider: WebSocket connected");
      };

      ws.onmessage = async (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "connection_ack") {
            const ack = message as ConnectionAckMessage;
            console.log(
              "StreamingDataProvider: Connection acknowledged for user:",
              ack.user_id
            );
            // Request initial data after connection is established
            requestFullSync();
          } else if (message.type === "sync_response") {
            await handleSyncResponse(message as SyncResponseMessage);
          } else if (message.type === "audit_log_event") {
            await handleAuditLogEvent(message as AuditLogEventMessage);
          } else if (message.type === "error") {
            const errorMsg = message as ErrorMessage;
            setError(new Error(errorMsg.message || "Unknown error"));
            console.error(
              "StreamingDataProvider: WebSocket error:",
              errorMsg.code,
              errorMsg.message
            );
          }
        } catch (err) {
          console.error(
            "StreamingDataProvider: Error parsing WebSocket message:",
            err
          );
        }
      };

      ws.onerror = (err) => {
        console.error("StreamingDataProvider: WebSocket error:", err);
        setError(new Error("Connection error occurred"));
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Only attempt to reconnect if the component is still mounted
        if (!isMounted) {
          return;
        }
        // Attempt to reconnect after 3 seconds
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
        }
        reconnectTimeout = window.setTimeout(() => {
          if (!isConnected() && isMounted) {
            connectWebSocket();
          }
        }, 3000);
      };
    } catch (err) {
      console.error("StreamingDataProvider: Error creating WebSocket:", err);
      setError(new Error("Failed to create WebSocket connection"));
      setIsConnected(false);
    }
  };

  // Request full sync
  const requestFullSync = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const request: SyncRequestMessage = {
      type: "sync_request",
      since_timestamp: null,
    };
    ws.send(JSON.stringify(request));
    setIsLoading(true);
  };

  // Request incremental sync
  const requestIncrementalSync = (sinceTimestamp: string) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const request: SyncRequestMessage = {
      type: "sync_request",
      since_timestamp: sinceTimestamp,
    };
    ws.send(JSON.stringify(request));
  };

  // Handle sync response
  const handleSyncResponse = async (message: SyncResponseMessage) => {
    setIsLoading(false);

    if (message.day_context) {
      // Full context - replace store
      setDayContextStore({ data: message.day_context });
      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
      setIsOutOfSync(false);
    } else if (message.changes) {
      // Incremental changes - apply to existing store
      applyChanges(message.changes);
      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
    }
  };

  // Apply incremental changes to store
  const applyChanges = (changes: EntityChange[]) => {
    setDayContextStore((current) => {
      if (!current.data) {
        // If no current context, we can't apply incremental changes
        // This shouldn't happen, but request full sync if it does
        requestFullSync();
        return current;
      }

      const updated = { ...current.data };
      const updatedTasks = [...(updated.tasks ?? [])];
      const updatedEvents = [
        ...(updated.calendar_entries ?? updated.events ?? []),
      ];

      for (const change of changes) {
        if (change.entity_type === "task") {
          const task = change.entity_data as Task;
          if (change.change_type === "created") {
            updatedTasks.push(task);
          } else if (change.change_type === "updated") {
            const index = updatedTasks.findIndex((t) => t.id === task.id);
            if (index >= 0) {
              updatedTasks[index] = task;
            } else {
              // Task not found, add it (might have been created before we loaded)
              updatedTasks.push(task);
            }
          } else if (change.change_type === "deleted") {
            const index = updatedTasks.findIndex(
              (t) => t.id === change.entity_id
            );
            if (index >= 0) {
              updatedTasks.splice(index, 1);
            }
          }
        } else if (change.entity_type === "calendar_entry") {
          const event = change.entity_data as Event;
          if (change.change_type === "created") {
            updatedEvents.push(event);
          } else if (change.change_type === "updated") {
            const index = updatedEvents.findIndex((e) => e.id === event.id);
            if (index >= 0) {
              updatedEvents[index] = event;
            } else {
              // Event not found, add it
              updatedEvents.push(event);
            }
          } else if (change.change_type === "deleted") {
            const index = updatedEvents.findIndex(
              (e) => e.id === change.entity_id
            );
            if (index >= 0) {
              updatedEvents.splice(index, 1);
            }
          }
        }
      }

      updated.tasks = updatedTasks;
      updated.calendar_entries = updatedEvents;
      updated.events = updatedEvents;

      return { data: updated };
    });
  };

  // Handle real-time audit log events
  const handleAuditLogEvent = async (message: AuditLogEventMessage) => {
    if (!message.audit_log) {
      return;
    }

    // If we haven't loaded initial data yet, ignore events
    if (!dayContextStore) {
      return;
    }

    const auditLog = message.audit_log;
    const occurredAt = auditLog.occurred_at;

    // Check for sync issues
    const lastTimestamp = lastProcessedTimestamp();
    if (lastTimestamp && occurredAt < lastTimestamp) {
      // Received older event than what we've already processed
      setIsOutOfSync(true);
      console.warn(
        "StreamingDataProvider: Out of sync detected - received older event"
      );
    }

    // Update timestamp (always move forward)
    if (!lastTimestamp || occurredAt > lastTimestamp) {
      setLastProcessedTimestamp(occurredAt);
    }

    // Apply the change based on audit log
    // We need to determine the change type from activity_type
    const activityType = auditLog.activity_type;
    let changeType: "created" | "updated" | "deleted" | null = null;

    if (
      activityType.includes("Created") ||
      activityType === "EntityCreatedEvent"
    ) {
      changeType = "created";
    } else if (
      activityType.includes("Deleted") ||
      activityType === "EntityDeletedEvent"
    ) {
      changeType = "deleted";
    } else if (
      activityType.includes("Updated") ||
      activityType === "EntityUpdatedEvent"
    ) {
      changeType = "updated";
    }

    if (!changeType || !auditLog.entity_type || !auditLog.entity_id) {
      // Can't process this event
      return;
    }

    // For created/updated, request incremental sync to get entity data
    // We debounce this to avoid too many requests
    if (changeType === "created" || changeType === "updated") {
      // Use a small delay to batch multiple rapid updates
      const syncDelay = 500; // 500ms debounce
      if (syncDebounceTimeout) {
        clearTimeout(syncDebounceTimeout);
      }
      syncDebounceTimeout = window.setTimeout(() => {
        const timestamp = lastProcessedTimestamp();
        if (timestamp) {
          requestIncrementalSync(timestamp);
        }
      }, syncDelay);
    } else if (changeType === "deleted") {
      // Apply deletion immediately
      setDayContextStore((current) => {
        if (!current.data) return current;

        const updated = { ...current.data };
        if (auditLog.entity_type === "task") {
          updated.tasks = (updated.tasks ?? []).filter(
            (t) => t.id !== auditLog.entity_id
          );
        } else if (auditLog.entity_type === "calendar_entry") {
          updated.calendar_entries = (updated.calendar_entries ?? []).filter(
            (e) => e.id !== auditLog.entity_id
          );
          updated.events = updated.calendar_entries;
        }

        return { data: updated };
      });
    }
  };

  // Optimistically update a task in the local state
  const updateTaskLocally = (updatedTask: Task) => {
    setDayContextStore((current) => {
      if (!current.data) return current;
      return {
        data: {
          ...current.data,
          tasks: (current.data.tasks ?? []).map((t) =>
            t.id === updatedTask.id ? updatedTask : t
          ),
        },
      };
    });
  };

  const setTaskStatus = async (
    task: Task,
    status: TaskStatus
  ): Promise<void> => {
    // Optimistic update
    const previousTask = task;
    updateTaskLocally({ ...task, status });

    try {
      const updatedTask = await taskAPI.setTaskStatus(task, status);
      updateTaskLocally(updatedTask);
    } catch (error) {
      // Rollback on error
      updateTaskLocally(previousTask);
      throw error;
    }
  };

  const sync = () => {
    requestFullSync();
  };

  const syncIncremental = (sinceTimestamp: string) => {
    requestIncrementalSync(sinceTimestamp);
  };

  // Connect on mount
  onMount(() => {
    isMounted = true;
    connectWebSocket();
  });

  // Cleanup on unmount
  onCleanup(() => {
    // Set isMounted to false first to prevent reconnection attempts
    isMounted = false;

    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
    }
    if (syncDebounceTimeout) {
      clearTimeout(syncDebounceTimeout);
    }
    if (ws) {
      ws.close();
    }
  });

  const value: StreamingDataContextValue = {
    dayContext,
    tasks,
    events,
    day,
    isLoading,
    error,
    isConnected,
    isOutOfSync,
    sync,
    syncIncremental,
    setTaskStatus,
  };

  return (
    <StreamingDataContext.Provider value={value}>
      {props.children}
    </StreamingDataContext.Provider>
  );
}

export function useStreamingData(): StreamingDataContextValue {
  const context = useContext(StreamingDataContext);
  if (!context) {
    throw new Error(
      "useStreamingData must be used within a StreamingDataProvider"
    );
  }
  return context;
}
