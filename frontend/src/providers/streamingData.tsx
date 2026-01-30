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
  Alarm,
  AlarmType,
  AlarmStatus,
  BrainDump,
  BrainDumpStatus,
  PushNotification,
  DayContextWithRoutines,
  Routine,
} from "@/types/api";
import {
  brainDumpAPI,
  notificationAPI,
  alarmAPI,
  reminderAPI,
  routineAPI,
  TaskActionPayload,
  taskAPI,
} from "@/utils/api";
import { getWebSocketBaseUrl, getWebSocketProtocol } from "@/utils/config";
import { globalNotifications } from "@/providers/notifications";
import AlarmTriggeredOverlay from "@/components/alarms/TriggeredOverlay";
import {
  applyEntityChanges,
  type EntityChange,
} from "@/providers/streaming/changeApplier";
import {
  buildChangeNotification,
  buildTaskCompletedNotification,
  countCompletedTasksFromChanges,
  countCompletedTasksFromFullSync,
} from "@/providers/streaming/notifications";
import {
  createWsClient,
  type DomainEventEnvelope,
  type WsClient,
} from "@/utils/wsClient";

interface StreamingDataContextValue {
  // The main data - provides loading/error states
  dayContext: Accessor<DayContextWithRoutines | undefined>;
  tasks: Accessor<Task[]>;
  events: Accessor<Event[]>;
  reminders: Accessor<Reminder[]>;
  alarms: Accessor<Alarm[]>;
  brainDumps: Accessor<BrainDump[]>;
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
    action: TaskActionPayload,
  ) => Promise<void>;
  addAdhocTask: (name: string, category: TaskCategory) => Promise<void>;
  addReminder: (name: string) => Promise<void>;
  updateReminderStatus: (
    reminder: Reminder,
    status: ReminderStatus,
  ) => Promise<void>;
  removeReminder: (reminderId: string) => Promise<void>;
  addAlarm: (payload: {
    name?: string;
    time: string;
    alarmType?: AlarmType;
    url?: string;
  }) => Promise<void>;
  snoozeAlarm: (alarm: Alarm, snoozedUntil: string) => Promise<void>;
  cancelAlarm: (alarm: Alarm) => Promise<void>;
  removeAlarm: (alarm: Alarm) => Promise<void>;
  addBrainDump: (text: string) => Promise<void>;
  updateBrainDumpStatus: (
    item: BrainDump,
    status: BrainDumpStatus,
  ) => Promise<void>;
  removeBrainDump: (itemId: string) => Promise<void>;
  loadNotifications: () => Promise<void>;
  subscribeToTopic: (
    topic: string,
    handler: (event: DomainEventEnvelope) => void,
  ) => () => void;
  unsubscribeFromTopic: (topic: string) => void;
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

const isOnMeRoute = (): boolean =>
  typeof window !== "undefined" && window.location.pathname.startsWith("/me");

export function StreamingDataProvider(props: ParentProps) {
  const [dayContextStore, setDayContextStore] = createStore<{
    data: DayContextWithRoutines | undefined;
  }>({ data: undefined });
  const [isLoading, setIsLoading] = createSignal(true);
  const [error, setError] = createSignal<Error | undefined>(undefined);
  const [isConnected, setIsConnected] = createSignal(false);
  const [isOutOfSync, setIsOutOfSync] = createSignal(false);
  const [notifications, setNotifications] = createSignal<PushNotification[]>(
    [],
  );
  const [notificationsLoading, setNotificationsLoading] = createSignal(false);
  const [lastProcessedTimestamp, setLastProcessedTimestamp] = createSignal<
    string | null
  >(null);

  const routines = createMemo(() => {
    const context = dayContextStore.data as DayContextWithRoutines | undefined;
    return context?.routines ?? [];
  });

  let syncDebounceTimeout: number | null = null;
  let isMounted = false;
  let wsClient: WsClient<DomainEventEnvelope> | null = null;

  type ReminderWithOptionalId = Omit<Reminder, "id"> & { id?: string | null };
  type BrainDumpWithOptionalId = Omit<BrainDump, "id"> & {
    id?: string | null;
  };

  const hasNonEmptyId = <T extends { id?: string | null }>(
    item: T,
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

  const normalizeBrainDumps = (
    items?: BrainDumpWithOptionalId[],
  ): BrainDump[] => (items ?? []).filter(hasNonEmptyId);

  const isSameAlarm = (left: Alarm, right: Alarm): boolean => {
    if (left.id && right.id) {
      return left.id === right.id;
    }
    return (
      left.name === right.name &&
      left.time === right.time &&
      left.type === right.type &&
      left.url === right.url
    );
  };

  // Derived values from the store
  const dayContext = createMemo(() => dayContextStore.data);
  const tasks = createMemo(() => dayContextStore.data?.tasks ?? []);
  const events = createMemo(() => dayContextStore.data?.calendar_entries ?? []);
  const reminders = createMemo(() => {
    // Reminders are stored on the day entity within day_context
    // Note: reminders may not be in the generated types yet, but they exist at runtime
    const day = dayContextStore.data?.day;
    if (!day) return [];
    return normalizeReminders(
      (day as { reminders?: ReminderWithOptionalId[] }).reminders,
    );
  });
  const alarms = createMemo(() => {
    const day = dayContextStore.data?.day;
    if (!day) return [];
    const allAlarms = (day as { alarms?: Alarm[] }).alarms ?? [];
    return allAlarms.filter(
      (alarm) => (alarm.status ?? "ACTIVE") !== "CANCELLED",
    );
  });
  const triggeredAlarm = createMemo<Alarm | undefined>(() => {
    const active = (alarms() ?? []).filter(
      (alarm) => (alarm.status ?? "ACTIVE") === "TRIGGERED",
    );
    if (active.length === 0) return undefined;
    return [...active].sort((a, b) => {
      const aTime = a.datetime
        ? new Date(a.datetime).getTime()
        : Number.MAX_SAFE_INTEGER;
      const bTime = b.datetime
        ? new Date(b.datetime).getTime()
        : Number.MAX_SAFE_INTEGER;
      return aTime - bTime;
    })[0];
  });
  const brainDumps = createMemo(() => {
    const day = dayContextStore.data?.day;
    if (!day) return [];
    return normalizeBrainDumps(
      (day as { brain_dump_items?: BrainDumpWithOptionalId[] })
        .brain_dump_items,
    );
  });
  const day = createMemo<Day | undefined>(() => {
    const currentDay = dayContextStore.data?.day;
    if (!currentDay) return undefined;
    return {
      ...currentDay,
      reminders: reminders(),
      alarms: alarms(),
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

  const getWebSocketUrl = (): string | null => {
    if (typeof window === "undefined" || typeof document === "undefined") {
      return null;
    }

    const protocol = getWebSocketProtocol();
    const baseUrl = getWebSocketBaseUrl();
    const token = getCookie("lykke_auth");

    let wsUrl = `${protocol}//${baseUrl}/days/today/context`;
    if (token) {
      wsUrl += `?token=${encodeURIComponent(token)}`;
    }

    return wsUrl;
  };

  const getOrCreateWsClient = (): WsClient<DomainEventEnvelope> | null => {
    if (wsClient) return wsClient;

    const url = getWebSocketUrl();
    if (!url) return null;

    wsClient = createWsClient<WebSocketMessage, DomainEventEnvelope>({
      url,
      reconnectDelayMs: 3000,
      shouldReconnect: () => isMounted,
      onOpen: () => {
        setIsConnected(true);
        setError(undefined);
        requestFullSync();
      },
      onClose: () => {
        setIsConnected(false);
      },
      onError: (err) => {
        console.error("StreamingDataProvider: WebSocket error:", err);
        setError(new Error("Connection error occurred"));
        setIsConnected(false);
      },
      onMessage: async (message) => {
        if (message.type === "connection_ack") {
          const ack = message as ConnectionAckMessage;
          console.log(
            "StreamingDataProvider: Connection acknowledged for user:",
            ack.user_id,
          );
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
            errorMsg.message,
          );
        }
      },
    });

    return wsClient;
  };

  // Connect to WebSocket
  const connectWebSocket = () => {
    setIsConnected(false);
    setError(undefined);
    getOrCreateWsClient()?.connect();
  };

  // Request full sync
  const requestFullSync = () => {
    const request: SyncRequestMessage = {
      type: "sync_request",
      since_timestamp: null,
    };
    const sent = getOrCreateWsClient()?.sendJson(request) ?? false;
    if (sent) {
      setIsLoading(true);
    }
  };

  // Request incremental sync
  const requestIncrementalSync = (sinceTimestamp: string) => {
    const request: SyncRequestMessage = {
      type: "sync_request",
      since_timestamp: sinceTimestamp,
    };
    getOrCreateWsClient()?.sendJson(request);
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
          message.day_context.tasks ?? [],
        );
        if (completedCount > 0) {
          globalNotifications.addInfo(
            buildTaskCompletedNotification(completedCount),
            {
              duration: 4000,
            },
          );
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
          message.changes,
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

      const result = applyEntityChanges(current.data, changes);
      didUpdate = result.didUpdate;

      if (!result.didUpdate) return current;
      return { data: result.nextContext };
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
        "StreamingDataProvider: Out of sync detected - received older event",
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
      activityType === "BrainDumpAddedEvent" ||
      activityType === "BrainDumpStatusChangedEvent" ||
      activityType === "BrainDumpRemovedEvent"
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
            (t) => t.id !== auditLog.entity_id,
          );
        } else if (
          auditLog.entity_type === "calendar_entry" ||
          auditLog.entity_type === "calendarentry"
        ) {
          updated.calendar_entries = (updated.calendar_entries ?? []).filter(
            (e) => e.id !== auditLog.entity_id,
          );
        } else if (auditLog.entity_type === "routine") {
          const routinesList =
            (updated as DayContextWithRoutines).routines ?? [];
          (updated as DayContextWithRoutines).routines = routinesList.filter(
            (routine) => routine.id !== auditLog.entity_id,
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
            t.id === updatedTask.id ? updatedTask : t,
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
    status: TaskStatus,
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
    snoozedUntil: string,
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
    action: TaskActionPayload,
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
        : t,
    );
    // Update all tasks locally
    updatedTasks.forEach((task) => updateTaskLocally(task));

    try {
      const updatedTasksFromAPI = await routineAPI.setRoutineAction(
        routineId,
        action,
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
    category: TaskCategory,
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

  const updateAlarmsLocally = (updatedAlarms: Alarm[]) => {
    setDayContextStore((current) => {
      if (!current.data || !current.data.day) return current;
      const updated = {
        data: {
          ...current.data,
          day: {
            ...current.data.day,
            alarms: updatedAlarms,
          },
        },
      };
      return updated;
    });
  };

  const updateAlarmLocally = (updatedAlarm: Alarm) => {
    const next = (alarms() ?? []).map((existing) =>
      isSameAlarm(existing, updatedAlarm) ? updatedAlarm : existing,
    );
    updateAlarmsLocally(next);
  };

  const updateBrainDumpsLocally = (updatedItems: BrainDump[]) => {
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
    status: ReminderStatus,
  ): Promise<void> => {
    // Optimistic update
    const previousReminders = reminders();
    const updatedReminders = previousReminders.map((r: Reminder) =>
      r.id === reminder.id ? { ...r, status } : r,
    );
    updateRemindersLocally(updatedReminders);

    try {
      const updatedReminder = await reminderAPI.updateReminderStatus(
        reminder.id,
        status,
      );
      const nextReminders = previousReminders.map((r: Reminder) =>
        r.id === updatedReminder.id ? updatedReminder : r,
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
    const updatedReminders = previousReminders.filter(
      (r: Reminder) => r.id !== reminderId,
    );
    updateRemindersLocally(updatedReminders);

    try {
      const removedReminder = await reminderAPI.removeReminder(reminderId);
      const nextReminders = previousReminders.filter(
        (r) => r.id !== removedReminder.id,
      );
      updateRemindersLocally(nextReminders);
    } catch (error) {
      // Rollback on error
      updateRemindersLocally(previousReminders);
      throw error;
    }
  };

  const addAlarm = async (payload: {
    name?: string;
    time: string;
    alarmType?: AlarmType;
    url?: string;
  }): Promise<void> => {
    const created = await alarmAPI.addAlarm({
      name: payload.name,
      time: payload.time,
      alarm_type: payload.alarmType,
      url: payload.url,
    });
    updateAlarmsLocally([...(alarms() ?? []), created]);
  };

  const setAlarmStatus = async (
    alarm: Alarm,
    status: AlarmStatus,
    snoozedUntil?: string | null,
  ): Promise<void> => {
    if (!alarm.id) {
      throw new Error("Alarm id is missing");
    }
    const previousAlarms = alarms();
    const optimisticAlarm: Alarm = {
      ...alarm,
      status,
      snoozed_until: snoozedUntil ?? null,
    };
    updateAlarmLocally(optimisticAlarm);

    try {
      const updatedAlarm = await alarmAPI.updateAlarmStatus({
        alarm_id: alarm.id,
        status,
        snoozed_until: snoozedUntil ?? undefined,
      });
      updateAlarmLocally(updatedAlarm);
    } catch (error) {
      updateAlarmsLocally(previousAlarms);
      throw error;
    }
  };

  const snoozeAlarm = async (
    alarm: Alarm,
    snoozedUntil: string,
  ): Promise<void> => {
    await setAlarmStatus(alarm, "SNOOZED", snoozedUntil);
  };

  const cancelAlarm = async (alarm: Alarm): Promise<void> => {
    await setAlarmStatus(alarm, "CANCELLED", null);
  };

  const removeAlarm = async (alarm: Alarm): Promise<void> => {
    const previousAlarms = alarms();
    const updatedAlarms = previousAlarms.filter(
      (existing) => !isSameAlarm(existing, alarm),
    );
    updateAlarmsLocally(updatedAlarms);

    try {
      const removedAlarm = await alarmAPI.removeAlarm({
        name: alarm.name,
        time: alarm.time,
        alarm_type: alarm.type,
        url: alarm.url,
      });
      const nextAlarms = previousAlarms.filter(
        (existing) => !isSameAlarm(existing, removedAlarm),
      );
      updateAlarmsLocally(nextAlarms);
    } catch (error) {
      updateAlarmsLocally(previousAlarms);
      throw error;
    }
  };

  const addBrainDump = async (text: string): Promise<void> => {
    const item = await brainDumpAPI.addItem(text);
    updateBrainDumpsLocally([...(brainDumps() ?? []), item]);
  };

  const updateBrainDumpStatus = async (
    item: BrainDump,
    status: BrainDumpStatus,
  ): Promise<void> => {
    if (!item.id) {
      return;
    }
    const previousItems = brainDumps();
    const updatedItems = previousItems.map((i) =>
      i.id === item.id ? { ...i, status } : i,
    );
    updateBrainDumpsLocally(updatedItems);

    try {
      const updatedItem = await brainDumpAPI.updateItemStatus(item.id, status);
      const nextItems = previousItems.map((existing) =>
        existing.id === updatedItem.id ? updatedItem : existing,
      );
      updateBrainDumpsLocally(nextItems);
    } catch (error) {
      updateBrainDumpsLocally(previousItems);
      throw error;
    }
  };

  const removeBrainDump = async (itemId: string): Promise<void> => {
    const previousItems = brainDumps();
    const updatedItems = previousItems.filter((i) => i.id !== itemId);
    updateBrainDumpsLocally(updatedItems);

    try {
      const removedItem = await brainDumpAPI.removeItem(itemId);
      const nextItems = previousItems.filter(
        (item) => item.id !== removedItem.id,
      );
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

  const subscribeToTopic = (
    topic: string,
    handler: (event: DomainEventEnvelope) => void,
  ) => {
    const client = getOrCreateWsClient();
    if (!client) return () => {};
    return client.subscribeTopic(topic, handler);
  };

  const unsubscribeFromTopic = (topic: string) => {
    getOrCreateWsClient()?.unsubscribeTopic(topic);
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

    if (syncDebounceTimeout) {
      clearTimeout(syncDebounceTimeout);
    }
    wsClient?.close();
    wsClient = null;
  });

  const value: StreamingDataContextValue = {
    dayContext,
    tasks,
    events,
    reminders,
    alarms,
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
    addAlarm,
    snoozeAlarm,
    cancelAlarm,
    removeAlarm,
    addBrainDump,
    updateBrainDumpStatus,
    removeBrainDump,
    loadNotifications,
    subscribeToTopic,
    unsubscribeFromTopic,
  };

  return (
    <StreamingDataContext.Provider value={value}>
      {props.children}
      <AlarmTriggeredOverlay
        alarm={triggeredAlarm()}
        isOpen={Boolean(triggeredAlarm())}
        onCancel={() => {
          const alarm = triggeredAlarm();
          if (!alarm) return;
          void cancelAlarm(alarm);
        }}
        onSnooze={(minutes) => {
          const alarm = triggeredAlarm();
          if (!alarm) return;
          const snoozedUntil = new Date(
            Date.now() + minutes * 60 * 1000,
          ).toISOString();
          void snoozeAlarm(alarm, snoozedUntil);
        }}
      />
    </StreamingDataContext.Provider>
  );
}

export function useStreamingData(): StreamingDataContextValue {
  const context = useContext(StreamingDataContext);
  if (!context) {
    throw new Error(
      "useStreamingData must be used within a StreamingDataProvider",
    );
  }
  return context;
}
