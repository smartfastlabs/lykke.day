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
import {
  DayContext,
  Task,
  TaskCategory,
  Event,
  Day,
  TaskStatus,
  Reminder,
  ReminderStatus,
  BrainDumpItem,
  BrainDumpItemStatus,
  Routine,
} from "@/types/api";
import { taskAPI, reminderAPI, brainDumpAPI, routineAPI } from "@/utils/api";
import { getWebSocketBaseUrl, getWebSocketProtocol } from "@/utils/config";

interface StreamingDataContextValue {
  // The main data - provides loading/error states
  dayContext: Accessor<DayContext | undefined>;
  tasks: Accessor<Task[]>;
  events: Accessor<Event[]>;
  reminders: Accessor<Reminder[]>;
  brainDumpItems: Accessor<BrainDumpItem[]>;
  day: Accessor<Day | undefined>;
  routines: Accessor<Routine[] | undefined>;
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
  setRoutineAction: (routineId: string, status: TaskStatus) => Promise<void>;
  addRoutineToToday: (routineId: string) => Promise<void>;
  addAdhocTask: (name: string, category: TaskCategory) => Promise<void>;
  addReminder: (name: string) => Promise<void>;
  updateReminderStatus: (reminder: Reminder, status: ReminderStatus) => Promise<void>;
  removeReminder: (reminderId: string) => Promise<void>;
  addBrainDumpItem: (text: string) => Promise<void>;
  updateBrainDumpItemStatus: (
    item: BrainDumpItem,
    status: BrainDumpItemStatus
  ) => Promise<void>;
  removeBrainDumpItem: (itemId: string) => Promise<void>;
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
  routines?: Routine[];
  last_audit_log_timestamp?: string | null;
}

// Deprecated: audit_log_event messages are no longer sent by the backend
// The backend now sends sync_response messages with changes for real-time updates
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
  entity_data: Task | Event | Routine | Routine | null;
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

  // Routines store - separate from day context since routines aren't date-specific
  const [routinesStore, setRoutinesStore] = createStore<{
    routines: Routine[];
  }>({ routines: [] });

  // Expose routines from store
  const routines = createMemo(() => routinesStore.routines);

  let ws: WebSocket | null = null;
  let reconnectTimeout: number | null = null;
  let syncDebounceTimeout: number | null = null;
  let isMounted = false;

  type ReminderWithOptionalId = Omit<Reminder, "id"> & { id?: string | null };
  type BrainDumpItemWithOptionalId = Omit<BrainDumpItem, "id"> & {
    id?: string | null;
  };

  const hasNonEmptyId = <T extends { id?: string | null }>(
    item: T
  ): item is T & { id: string } =>
    typeof item.id === "string" && item.id.length > 0;

  const normalizeReminders = (items?: ReminderWithOptionalId[]): Reminder[] =>
    (items ?? []).filter(hasNonEmptyId);

  const normalizeBrainDumpItems = (
    items?: BrainDumpItemWithOptionalId[]
  ): BrainDumpItem[] => (items ?? []).filter(hasNonEmptyId);

  // Derived values from the store
  const dayContext = createMemo(() => dayContextStore.data);
  const tasks = createMemo(() => dayContextStore.data?.tasks ?? []);
  const events = createMemo(
    () =>
      dayContextStore.data?.calendar_entries ??
      dayContextStore.data?.events ??
      []
  );
  const reminders = createMemo(() => {
    // Reminders are stored on the day entity within day_context
    // Note: reminders may not be in the generated types yet, but they exist at runtime
    const day = dayContextStore.data?.day;
    if (!day) return [];
    return normalizeReminders((day as { reminders?: ReminderWithOptionalId[] }).reminders);
  });
  const brainDumpItems = createMemo(() => {
    const day = dayContextStore.data?.day;
    if (!day) return [];
    return normalizeBrainDumpItems(
      (day as { brain_dump_items?: BrainDumpItemWithOptionalId[] })
        .brain_dump_items
    );
  });
  const day = createMemo<Day | undefined>(() => {
    const currentDay = dayContextStore.data?.day;
    if (!currentDay) return undefined;
    return {
      ...currentDay,
      reminders: reminders(),
      brain_dump_items: brainDumpItems(),
    };
  });

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
        console.log("StreamingDataProvider: Requesting full sync");
        requestFullSync();
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
            // Sync request is now handled in onopen to ensure WebSocket is ready
            // This prevents race conditions
          } else if (message.type === "sync_response") {
            await handleSyncResponse(message as SyncResponseMessage);
          } else if (message.type === "audit_log_event") {
            // Deprecated: This handler is kept for backward compatibility
            // The backend now sends sync_response messages for real-time updates
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
        // Capture current state values to avoid reactivity warnings
        const currentlyConnected = isConnected();
        reconnectTimeout = window.setTimeout(() => {
          if (!currentlyConnected && isMounted) {
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

      // Update routines from full sync response
      if (message.routines) {
        setRoutinesStore({ routines: message.routines });
      }
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
    // Track routine updates separately since they're in a different store
    let updatedRoutines: Routine[] | null = null;

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
        } else if (
          change.entity_type === "calendar_entry" ||
          change.entity_type === "calendarentry"
        ) {
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
        } else if (change.entity_type === "routine") {
          const routine = change.entity_data as Routine;
          // Initialize updatedRoutines if not already done
          if (updatedRoutines === null) {
            updatedRoutines = [...routinesStore.routines];
          }

          if (change.change_type === "created") {
            updatedRoutines.push(routine);
          } else if (change.change_type === "updated") {
            updatedRoutines = updatedRoutines.map((r) =>
              r.id === routine.id ? routine : r
            );
          } else if (change.change_type === "deleted") {
            updatedRoutines = updatedRoutines.filter(
              (r) => r.id !== change.entity_id
            );
          }
        } else if (change.entity_type === "day") {
          const updatedDay = change.entity_data as Day;
          if (change.change_type === "updated" || change.change_type === "created") {
            updated.day = updatedDay;
          }
        }
      }

      updated.tasks = updatedTasks;
      updated.calendar_entries = updatedEvents;
      updated.events = updatedEvents;

      return { data: updated };
    });

    // Update routines store if routines were modified
    if (updatedRoutines !== null) {
      setRoutinesStore({ routines: updatedRoutines });
    }
  };

  // Handle real-time audit log events
  // Deprecated: This handler is for backward compatibility only
  // The backend now sends sync_response messages with changes for real-time updates
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
      activityType === "EntityUpdatedEvent" ||
      activityType === "BrainDumpItemAddedEvent" ||
      activityType === "BrainDumpItemStatusChangedEvent" ||
      activityType === "BrainDumpItemRemovedEvent"
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
      // Use occurredAt directly since we just updated the timestamp to this value
      // This avoids reactivity warnings and ensures we use the correct timestamp
      const timestampToUse = occurredAt;
      syncDebounceTimeout = window.setTimeout(() => {
        requestIncrementalSync(timestampToUse);
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
        } else if (
          auditLog.entity_type === "calendar_entry" ||
          auditLog.entity_type === "calendarentry"
        ) {
          updated.calendar_entries = (updated.calendar_entries ?? []).filter(
            (e) => e.id !== auditLog.entity_id
          );
          updated.events = updated.calendar_entries;
        } else if (auditLog.entity_type === "routine") {
          setRoutinesStore((current) => {
            const updated = {
              routines: current.routines.filter(
                (r) => r.id !== auditLog.entity_id
              ),
            };
            return updated;
          });
          return current;
        }

        return { data: updated };
      });
    }
  };

  // Optimistically update a task in the local state
  const updateTaskLocally = (updatedTask: Task) => {
    setDayContextStore((current) => {
      if (!current.data) return current;
      const updated = {
        data: {
          ...current.data,
          tasks: (current.data.tasks ?? []).map((t) =>
            t.id === updatedTask.id ? updatedTask : t
          ),
        },
      };
      return updated;
    });
  };

  const addTaskLocally = (task: Task) => {
    setDayContextStore((current) => {
      if (!current.data) return current;
      const updated = {
        data: {
          ...current.data,
          tasks: [...(current.data.tasks ?? []), task],
        },
      };
      return updated;
    });
  };

  const upsertTasksLocally = (incomingTasks: Task[]) => {
    setDayContextStore((current) => {
      if (!current.data) return current;
      const existingTasks = current.data.tasks ?? [];
      const taskMap = new Map(existingTasks.map((task) => [task.id, task]));
      incomingTasks.forEach((task) => taskMap.set(task.id, task));
      return {
        data: {
          ...current.data,
          tasks: Array.from(taskMap.values()),
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

  const setRoutineAction = async (
    routineId: string,
    status: TaskStatus
  ): Promise<void> => {
    // Optimistic update: update all tasks with this routine_id
    const previousTasks = tasks();
    const updatedTasks = previousTasks.map((t: Task) =>
      t.routine_id === routineId ? { ...t, status } : t
    );
    // Update all tasks locally
    updatedTasks.forEach((task) => updateTaskLocally(task));

    try {
      const updatedTasksFromAPI = await routineAPI.setRoutineAction(
        routineId,
        status
      );
      // Update each task with the API response
      updatedTasksFromAPI.forEach((task) => updateTaskLocally(task));
    } catch (error) {
      // Rollback on error
      previousTasks.forEach((task) => updateTaskLocally(task));
      throw error;
    }
  };

  const addRoutineToToday = async (routineId: string): Promise<void> => {
    const tasksFromAPI = await routineAPI.addToToday(routineId);
    upsertTasksLocally(tasksFromAPI);
  };

  const addAdhocTask = async (
    name: string,
    category: TaskCategory
  ): Promise<void> => {
    const currentDay = day();
    if (!currentDay) {
      throw new Error("Day context not loaded");
    }
    const created = await taskAPI.createAdhocTask({
      scheduled_date: currentDay.date,
      name,
      category,
    });
    addTaskLocally(created);
  };

  // Optimistically update reminders in local state
  const updateRemindersLocally = (updatedReminders: Reminder[]) => {
    setDayContextStore((current) => {
      if (!current.data || !current.data.day) return current;
      const updated = {
        data: {
          ...current.data,
          day: {
            ...current.data.day,
            reminders: updatedReminders,
          },
        },
      };
      return updated;
    });
  };

  const updateBrainDumpItemsLocally = (updatedItems: BrainDumpItem[]) => {
    setDayContextStore((current) => {
      if (!current.data || !current.data.day) return current;
      const updated = {
        data: {
          ...current.data,
          day: {
            ...current.data.day,
            brain_dump_items: updatedItems,
          },
        },
      };
      return updated;
    });
  };

  const addReminder = async (name: string): Promise<void> => {
    const reminder = await reminderAPI.addReminder(name);
    updateRemindersLocally([...(reminders() ?? []), reminder]);
  };

  const updateReminderStatus = async (
    reminder: Reminder,
    status: ReminderStatus
  ): Promise<void> => {
    // Optimistic update
    const previousReminders = reminders();
    const updatedReminders = previousReminders.map((r: Reminder) =>
      r.id === reminder.id ? { ...r, status } : r
    );
    updateRemindersLocally(updatedReminders);

    try {
      const updatedReminder = await reminderAPI.updateReminderStatus(
        reminder.id,
        status
      );
      const nextReminders = previousReminders.map((r: Reminder) =>
        r.id === updatedReminder.id ? updatedReminder : r
      );
      updateRemindersLocally(nextReminders);
    } catch (error) {
      // Rollback on error
      updateRemindersLocally(previousReminders);
      throw error;
    }
  };

  const removeReminder = async (reminderId: string): Promise<void> => {
    // Optimistic update
    const previousReminders = reminders();
    const updatedReminders = previousReminders.filter((r: Reminder) => r.id !== reminderId);
    updateRemindersLocally(updatedReminders);

    try {
      const removedReminder = await reminderAPI.removeReminder(reminderId);
      const nextReminders = previousReminders.filter(
        (r) => r.id !== removedReminder.id
      );
      updateRemindersLocally(nextReminders);
    } catch (error) {
      // Rollback on error
      updateRemindersLocally(previousReminders);
      throw error;
    }
  };

  const addBrainDumpItem = async (text: string): Promise<void> => {
    const item = await brainDumpAPI.addItem(text);
    updateBrainDumpItemsLocally([...(brainDumpItems() ?? []), item]);
  };

  const updateBrainDumpItemStatus = async (
    item: BrainDumpItem,
    status: BrainDumpItemStatus
  ): Promise<void> => {
    const previousItems = brainDumpItems();
    const updatedItems = previousItems.map((i) =>
      i.id === item.id ? { ...i, status } : i
    );
    updateBrainDumpItemsLocally(updatedItems);

    try {
      const updatedItem = await brainDumpAPI.updateItemStatus(item.id, status);
      const nextItems = previousItems.map((existing) =>
        existing.id === updatedItem.id ? updatedItem : existing
      );
      updateBrainDumpItemsLocally(nextItems);
    } catch (error) {
      updateBrainDumpItemsLocally(previousItems);
      throw error;
    }
  };

  const removeBrainDumpItem = async (itemId: string): Promise<void> => {
    const previousItems = brainDumpItems();
    const updatedItems = previousItems.filter((i) => i.id !== itemId);
    updateBrainDumpItemsLocally(updatedItems);

    try {
      const removedItem = await brainDumpAPI.removeItem(itemId);
      const nextItems = previousItems.filter((item) => item.id !== removedItem.id);
      updateBrainDumpItemsLocally(nextItems);
    } catch (error) {
      updateBrainDumpItemsLocally(previousItems);
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
    reminders,
    brainDumpItems,
    day,
    routines,
    isLoading,
    error,
    isConnected,
    isOutOfSync,
    sync,
    syncIncremental,
    setTaskStatus,
    setRoutineAction,
    addRoutineToToday,
    addAdhocTask,
    addReminder,
    updateReminderStatus,
    removeReminder,
    addBrainDumpItem,
    updateBrainDumpItemStatus,
    removeBrainDumpItem,
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
