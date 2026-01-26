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
  Task,
  TaskCategory,
  Event,
  Day,
  TaskStatus,
  Reminder,
  ReminderStatus,
  BrainDumpItem,
  BrainDumpItemStatus,
  PushNotification,
  DayContextWithRoutines,
  Routine,
} from "@/types/api";
import {
  brainDumpAPI,
  notificationAPI,
  reminderAPI,
  routineAPI,
  TaskActionPayload,
  taskAPI,
} from "@/utils/api";
import { getWebSocketBaseUrl, getWebSocketProtocol } from "@/utils/config";
import { globalNotifications } from "@/providers/notifications";

interface StreamingDataContextValue {
  // The main data - provides loading/error states
  dayContext: Accessor<DayContextWithRoutines | undefined>;
  tasks: Accessor<Task[]>;
  events: Accessor<Event[]>;
  reminders: Accessor<Reminder[]>;
  brainDumps: Accessor<BrainDumpItem[]>;
  notifications: Accessor<PushNotification[]>;
  day: Accessor<Day | undefined>;
  routines: Accessor<Routine[]>;
  // Loading and error states
  isLoading: Accessor<boolean>;
  notificationsLoading: Accessor<boolean>;
  error: Accessor<Error | undefined>;
  // Connection state
  isConnected: Accessor<boolean>;
  isOutOfSync: Accessor<boolean>;
  // Actions
  sync: () => void;
  syncIncremental: (sinceTimestamp: string) => void;
  setTaskStatus: (task: Task, status: TaskStatus) => Promise<void>;
  snoozeTask: (task: Task, snoozedUntil: string) => Promise<void>;
  setRoutineAction: (
    routineId: string,
    routineDefinitionId: string,
    action: TaskActionPayload
  ) => Promise<void>;
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
  loadNotifications: () => Promise<void>;
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
  day_context?: DayContextWithRoutines;
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
  entity_data: Task | Event | Routine | null;
}

const isOnMeRoute = (): boolean =>
  typeof window !== "undefined" && window.location.pathname.startsWith("/me");

const getEntityLabel = (entityType: string): string => {
  if (entityType === "calendar_entry" || entityType === "calendarentry") {
    return "event";
  }
  if (entityType === "task") return "task";
  if (entityType === "routine") return "routine";
  if (entityType === "day") return "day";
  return entityType.replace(/_/g, " ");
};

const getChangeVerb = (changeType: EntityChange["change_type"]): string => {
  if (changeType === "created") return "added";
  if (changeType === "updated") return "updated";
  return "removed";
};

const pluralize = (count: number, noun: string): string =>
  count === 1 ? noun : `${noun}s`;

const stableStringify = (value: unknown): string => {
  if (value === null || value === undefined) {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const keys = Object.keys(record).sort();
    return `{${keys
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
};

const areEntitiesEqual = (left: unknown, right: unknown): boolean =>
  stableStringify(left) === stableStringify(right);

const buildChangeNotification = (changes: EntityChange[]): string | null => {
  if (changes.length === 0) return null;

  const counts = new Map<string, number>();

  for (const change of changes) {
    const key = `${getEntityLabel(change.entity_type)}|${getChangeVerb(
      change.change_type
    )}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const parts = Array.from(counts.entries()).map(([key, count]) => {
    const [entityLabel, changeVerb] = key.split("|");
    return `${count} ${pluralize(count, entityLabel)} ${changeVerb}`;
  });

  if (parts.length === 0) return null;

  const maxParts = 3;
  const shownParts = parts.slice(0, maxParts);
  const remaining = parts.length - shownParts.length;
  const suffix = remaining > 0 ? `, and ${remaining} more updates` : "";

  return `Background update: ${shownParts.join(", ")}${suffix}.`;
};

const countCompletedTasksFromChanges = (
  current: DayContextWithRoutines,
  changes: EntityChange[]
): number => {
  const existingTasks = current.tasks ?? [];
  let completedCount = 0;

  for (const change of changes) {
    if (change.entity_type !== "task") continue;
    if (change.change_type !== "updated") continue;
    const task = change.entity_data as Task | null;
    if (!task || !task.id) continue;
    const previous = existingTasks.find((existing) => existing.id === task.id);
    if (previous?.status !== "COMPLETE" && task.status === "COMPLETE") {
      completedCount += 1;
    }
  }

  return completedCount;
};

const countCompletedTasksFromFullSync = (
  previousTasks: Task[],
  nextTasks: Task[]
): number => {
  const previousById = new Map(previousTasks.map((task) => [task.id, task]));
  let completedCount = 0;

  for (const task of nextTasks) {
    const previous = task.id ? previousById.get(task.id) : undefined;
    if (previous?.status !== "COMPLETE" && task.status === "COMPLETE") {
      completedCount += 1;
    }
  }

  return completedCount;
};

const buildTaskCompletedNotification = (count: number): string =>
  count === 1
    ? "Background update: 1 task completed."
    : `Background update: ${count} tasks completed.`;

export function StreamingDataProvider(props: ParentProps) {
  const [dayContextStore, setDayContextStore] = createStore<{
    data: DayContextWithRoutines | undefined;
  }>({ data: undefined });
  const [isLoading, setIsLoading] = createSignal(true);
  const [error, setError] = createSignal<Error | undefined>(undefined);
  const [isConnected, setIsConnected] = createSignal(false);
  const [isOutOfSync, setIsOutOfSync] = createSignal(false);
  const [notifications, setNotifications] = createSignal<PushNotification[]>([]);
  const [notificationsLoading, setNotificationsLoading] = createSignal(false);
  const [lastProcessedTimestamp, setLastProcessedTimestamp] = createSignal<
    string | null
  >(null);

  const routines = createMemo(() => {
    const context = dayContextStore.data as DayContextWithRoutines | undefined;
    return context?.routines ?? [];
  });

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

  const dedupeById = <T extends { id?: string | null }>(items: T[]): T[] => {
    const seen = new Set<string>();
    const deduped: T[] = [];
    for (const item of items) {
      if (!item.id) {
        deduped.push(item);
        continue;
      }
      if (seen.has(item.id)) {
        continue;
      }
      seen.add(item.id);
      deduped.push(item);
    }
    return deduped;
  };

  const normalizeReminders = (items?: ReminderWithOptionalId[]): Reminder[] =>
    dedupeById((items ?? []).filter(hasNonEmptyId));

  const normalizeBrainDumpItems = (
    items?: BrainDumpItemWithOptionalId[]
  ): BrainDumpItem[] => (items ?? []).filter(hasNonEmptyId);

  // Derived values from the store
  const dayContext = createMemo(() => dayContextStore.data);
  const tasks = createMemo(() => dayContextStore.data?.tasks ?? []);
  const events = createMemo(() => dayContextStore.data?.calendar_entries ?? []);
  const reminders = createMemo(() => {
    // Reminders are stored on the day entity within day_context
    // Note: reminders may not be in the generated types yet, but they exist at runtime
    const day = dayContextStore.data?.day;
    if (!day) return [];
    return normalizeReminders((day as { reminders?: ReminderWithOptionalId[] }).reminders);
  });
  const brainDumps = createMemo(() => {
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
      brain_dump_items: brainDumps(),
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
      const previousContext = dayContextStore.data;
      // Full context - replace store
      setDayContextStore({ data: message.day_context });

      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
      setIsOutOfSync(false);

      // Update routines if provided separately
      if (message.routines) {
        setDayContextStore((current) => {
          if (!current.data) return current;
          return {
            data: {
              ...current.data,
              routines: message.routines,
            },
          };
        });
      }

      if (isOnMeRoute() && previousContext) {
        const completedCount = countCompletedTasksFromFullSync(
          previousContext.tasks ?? [],
          message.day_context.tasks ?? []
        );
        if (completedCount > 0) {
          globalNotifications.addInfo(buildTaskCompletedNotification(completedCount), {
            duration: 4000,
          });
        }
      }
    } else if (message.changes) {
      const currentContext = dayContextStore.data;
      // Incremental changes - apply to existing store
      const didApplyChanges = applyChanges(message.changes);
      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
      if (didApplyChanges && isOnMeRoute() && currentContext) {
        const completedCount = countCompletedTasksFromChanges(
          currentContext,
          message.changes
        );
        const notification =
          completedCount > 0
            ? buildTaskCompletedNotification(completedCount)
            : buildChangeNotification(message.changes);
        if (notification) {
          globalNotifications.addInfo(notification, { duration: 4000 });
        }
      }
    }
  };

  // Apply incremental changes to store
  const applyChanges = (changes: EntityChange[]): boolean => {
    let didUpdate = false;
    setDayContextStore((current) => {
      if (!current.data) {
        // If no current context, we can't apply incremental changes
        // This shouldn't happen, but request full sync if it does
        requestFullSync();
        return current;
      }

      const updated = { ...current.data };
      const updatedTasks = [...(updated.tasks ?? [])];
      const updatedEvents = [...(updated.calendar_entries ?? [])];
      const updatedRoutines = [
        ...((updated as DayContextWithRoutines).routines ?? []),
      ];

      for (const change of changes) {
        if (change.entity_type === "task") {
          if (change.change_type === "deleted") {
            const index = updatedTasks.findIndex(
              (t) => t.id === change.entity_id
            );
            if (index >= 0) {
              updatedTasks.splice(index, 1);
              didUpdate = true;
            }
            continue;
          }
          const task = change.entity_data as Task | null;
          if (!task) {
            continue;
          }
          if (change.change_type === "created") {
            const index = updatedTasks.findIndex((t) => t.id === task.id);
            if (index >= 0) {
              if (!areEntitiesEqual(updatedTasks[index], task)) {
                updatedTasks[index] = task;
                didUpdate = true;
              }
            } else {
              updatedTasks.push(task);
              didUpdate = true;
            }
          } else if (change.change_type === "updated") {
            const index = updatedTasks.findIndex((t) => t.id === task.id);
            if (index >= 0) {
              if (!areEntitiesEqual(updatedTasks[index], task)) {
                updatedTasks[index] = task;
                didUpdate = true;
              }
            } else {
              // Task not found, add it (might have been created before we loaded)
              updatedTasks.push(task);
              didUpdate = true;
            }
          }
        } else if (
          change.entity_type === "calendar_entry" ||
          change.entity_type === "calendarentry"
        ) {
          if (change.change_type === "deleted") {
            const index = updatedEvents.findIndex(
              (e) => e.id === change.entity_id
            );
            if (index >= 0) {
              updatedEvents.splice(index, 1);
              didUpdate = true;
            }
            continue;
          }
          const event = change.entity_data as Event | null;
          if (!event) {
            continue;
          }
          if (change.change_type === "created") {
            const index = updatedEvents.findIndex((e) => e.id === event.id);
            if (index >= 0) {
              if (!areEntitiesEqual(updatedEvents[index], event)) {
                updatedEvents[index] = event;
                didUpdate = true;
              }
            } else {
              updatedEvents.push(event);
              didUpdate = true;
            }
          } else if (change.change_type === "updated") {
            const index = updatedEvents.findIndex((e) => e.id === event.id);
            if (index >= 0) {
              if (!areEntitiesEqual(updatedEvents[index], event)) {
                updatedEvents[index] = event;
                didUpdate = true;
              }
            } else {
              // Event not found, add it
              updatedEvents.push(event);
              didUpdate = true;
            }
          }
        } else if (change.entity_type === "routine") {
          if (change.change_type === "deleted") {
            const index = updatedRoutines.findIndex(
              (item) => item.id === change.entity_id
            );
            if (index >= 0) {
              updatedRoutines.splice(index, 1);
              didUpdate = true;
            }
            continue;
          }
          const routine = change.entity_data as Routine | null;
          if (!routine) {
            continue;
          }
          if (change.change_type === "created") {
            const index = updatedRoutines.findIndex((item) => item.id === routine.id);
            if (index >= 0) {
              if (!areEntitiesEqual(updatedRoutines[index], routine)) {
                updatedRoutines[index] = routine;
                didUpdate = true;
              }
            } else {
              updatedRoutines.push(routine);
              didUpdate = true;
            }
          } else if (change.change_type === "updated") {
            const index = updatedRoutines.findIndex((item) => item.id === routine.id);
            if (index >= 0) {
              if (!areEntitiesEqual(updatedRoutines[index], routine)) {
                updatedRoutines[index] = routine;
                didUpdate = true;
              }
            } else {
              updatedRoutines.push(routine);
              didUpdate = true;
            }
          }
        } else if (change.entity_type === "day") {
          const updatedDay = change.entity_data as Day | null;
          if (
            updatedDay &&
            (change.change_type === "updated" || change.change_type === "created")
          ) {
            if (!areEntitiesEqual(updated.day, updatedDay)) {
              updated.day = updatedDay;
              didUpdate = true;
            }
          }
        }
      }

      if (!didUpdate) {
        return current;
      }

      updated.tasks = updatedTasks;
      updated.calendar_entries = updatedEvents;
      (updated as DayContextWithRoutines).routines = updatedRoutines;

      return { data: updated };
    });
    return didUpdate;
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
        } else if (auditLog.entity_type === "routine") {
          const routinesList = (updated as DayContextWithRoutines).routines ?? [];
          (updated as DayContextWithRoutines).routines = routinesList.filter(
            (routine) => routine.id !== auditLog.entity_id
          );
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
      if (current.data.tasks?.some((existing) => existing.id === task.id)) {
        return current;
      }
      const updated = {
        data: {
          ...current.data,
          tasks: [...(current.data.tasks ?? []), task],
        },
      };
      return updated;
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

  const snoozeTask = async (
    task: Task,
    snoozedUntil: string
  ): Promise<void> => {
    if (!task.id) {
      throw new Error("Task id is missing");
    }
    const previousTask = task;
    updateTaskLocally({
      ...task,
      status: "SNOOZE",
      snoozed_until: snoozedUntil,
    });

    try {
      const updatedTask = await taskAPI.recordTaskAction(task.id, {
        type: "SNOOZE",
        data: { snoozed_until: snoozedUntil },
      });
      updateTaskLocally(updatedTask);
    } catch (error) {
      updateTaskLocally(previousTask);
      throw error;
    }
  };

  const setRoutineAction = async (
    routineId: string,
    routineDefinitionId: string,
    action: TaskActionPayload
  ): Promise<void> => {
    // Optimistic update: update all tasks with this routine_definition_id
    const previousTasks = tasks();
    const snoozedUntil =
      action.type === "SNOOZE" ? action.data?.snoozed_until : undefined;
    const updatedTasks = previousTasks.map((t: Task) =>
      t.routine_definition_id === routineDefinitionId
        ? {
            ...t,
            status: action.type as TaskStatus,
            snoozed_until: snoozedUntil ?? t.snoozed_until,
          }
        : t
    );
    // Update all tasks locally
    updatedTasks.forEach((task) => updateTaskLocally(task));

    try {
      const updatedTasksFromAPI = await routineAPI.setRoutineAction(
        routineId,
        action
      );
      // Update each task with the API response
      updatedTasksFromAPI.forEach((task) => updateTaskLocally(task));
    } catch (error) {
      // Rollback on error
      previousTasks.forEach((task) => updateTaskLocally(task));
      throw error;
    }
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
            reminders: dedupeById(updatedReminders),
          },
        },
      };
      return updated;
    });
  };

  const updateBrainDumpsLocally = (updatedItems: BrainDumpItem[]) => {
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
    updateBrainDumpsLocally([...(brainDumps() ?? []), item]);
  };

  const updateBrainDumpItemStatus = async (
    item: BrainDumpItem,
    status: BrainDumpItemStatus
  ): Promise<void> => {
    if (!item.id) {
      return;
    }
    const previousItems = brainDumps();
    const updatedItems = previousItems.map((i) =>
      i.id === item.id ? { ...i, status } : i
    );
    updateBrainDumpsLocally(updatedItems);

    try {
      const updatedItem = await brainDumpAPI.updateItemStatus(item.id, status);
      const nextItems = previousItems.map((existing) =>
        existing.id === updatedItem.id ? updatedItem : existing
      );
      updateBrainDumpsLocally(nextItems);
    } catch (error) {
      updateBrainDumpsLocally(previousItems);
      throw error;
    }
  };

  const removeBrainDumpItem = async (itemId: string): Promise<void> => {
    const previousItems = brainDumps();
    const updatedItems = previousItems.filter((i) => i.id !== itemId);
    updateBrainDumpsLocally(updatedItems);

    try {
      const removedItem = await brainDumpAPI.removeItem(itemId);
      const nextItems = previousItems.filter((item) => item.id !== removedItem.id);
      updateBrainDumpsLocally(nextItems);
    } catch (error) {
      updateBrainDumpsLocally(previousItems);
      throw error;
    }
  };

  const sync = () => {
    requestFullSync();
  };

  const syncIncremental = (sinceTimestamp: string) => {
    requestIncrementalSync(sinceTimestamp);
  };

  const loadNotifications = async () => {
    if (notificationsLoading()) {
      return;
    }
    setNotificationsLoading(true);
    try {
      const items = await notificationAPI.getToday();
      setNotifications(items);
    } catch (err) {
      console.error("StreamingDataProvider: Failed to load notifications", err);
    } finally {
      setNotificationsLoading(false);
    }
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
    brainDumps,
    notifications,
    day,
    routines,
    isLoading,
    notificationsLoading,
    error,
    isConnected,
    isOutOfSync,
    sync,
    syncIncremental,
    setTaskStatus,
    snoozeTask,
    setRoutineAction,
    addAdhocTask,
    addReminder,
    updateReminderStatus,
    removeReminder,
    addBrainDumpItem,
    updateBrainDumpItemStatus,
    removeBrainDumpItem,
    loadNotifications,
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
