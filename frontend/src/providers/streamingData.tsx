import {
  createContext,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
  untrack,
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
  Alarm,
  AlarmType,
  AlarmStatus,
  BrainDump,
  BrainDumpStatus,
  PushNotification,
  Message,
  DayContextWithRoutines,
  Routine,
} from "@/types/api";
import {
  alarmAPI,
  brainDumpAPI,
  routineAPI,
  TaskActionPayload,
  taskAPI,
  calendarEntryAPI,
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
  reminders: Accessor<Task[]>;
  alarms: Accessor<Alarm[]>;
  brainDumps: Accessor<BrainDump[]>;
  notifications: Accessor<PushNotification[]>;
  messages: Accessor<Message[]>;
  day: Accessor<Day | undefined>;
  routines: Accessor<Routine[]>;
  // Loading and error states
  isLoading: Accessor<boolean>;
  isPartLoading: (part: DayContextPartKey) => boolean;
  notificationsLoading: Accessor<boolean>;
  messagesLoading: Accessor<boolean>;
  error: Accessor<Error | undefined>;
  // Connection state
  isConnected: Accessor<boolean>;
  isOutOfSync: Accessor<boolean>;
  lastProcessedTimestamp: Accessor<string | null>;
  lastChangeStreamId: Accessor<string | null>;
  debugEvents: Accessor<StreamingDebugEvent[]>;
  clearDebugEvents: () => void;
  // Actions
  sync: () => void;
  syncIncremental: (sinceTimestamp: string) => void;
  setTaskStatus: (task: Task, status: TaskStatus) => Promise<void>;
  snoozeTask: (task: Task, snoozedUntil: string) => Promise<void>;
  rescheduleTask: (task: Task, scheduledDate: string) => Promise<void>;
  setRoutineAction: (
    routineId: string,
    routineDefinitionId: string,
    action: TaskActionPayload,
  ) => Promise<void>;
  addAdhocTask: (name: string, category: TaskCategory) => Promise<void>;
  addReminder: (name: string) => Promise<void>;
  updateReminderStatus: (reminder: Task, status: TaskStatus) => Promise<void>;
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
  loadMessages: () => Promise<void>;
  updateEventAttendanceStatus: (
    event: Event,
    status: import("@/types/api").CalendarEntryAttendanceStatus | null,
  ) => Promise<void>;
  subscribeToTopic: (
    topic: string,
    handler: (event: DomainEventEnvelope) => void,
  ) => () => void;
  unsubscribeFromTopic: (topic: string) => void;
}

const StreamingDataContext = createContext<StreamingDataContextValue>();

interface StreamingDebugEvent {
  id: string;
  timestamp: string;
  direction: "in" | "out" | "state" | "error";
  label: string;
  payload?: unknown;
}

// WebSocket message types
interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

type DayContextPartKey =
  | "day"
  | "tasks"
  | "calendar_entries"
  | "routines"
  | "brain_dumps"
  | "push_notifications"
  | "messages";

type DayContextLoadingState = Record<DayContextPartKey, boolean>;

interface PartialDayContext {
  day?: Day;
  calendar_entries?: Event[];
  tasks?: Task[];
  routines?: Routine[];
  brain_dumps?: BrainDump[];
  push_notifications?: PushNotification[];
  messages?: Message[];
}

interface SyncRequestMessage extends WebSocketMessage {
  type: "sync_request";
  since_timestamp?: string | null;
  since_change_stream_id?: string | null;
  partial_key?: DayContextPartKey | null;
  partial_keys?: DayContextPartKey[] | null;
}

interface SyncResponseMessage extends WebSocketMessage {
  type: "sync_response";
  day_context?: DayContextWithRoutines;
  changes?: EntityChange[];
  partial_context?: PartialDayContext;
  partial_key?: DayContextPartKey | null;
  sync_complete?: boolean | null;
  last_audit_log_timestamp?: string | null;
  last_change_stream_id?: string | null;
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
  const [dayContextLoading, setDayContextLoading] =
    createStore<DayContextLoadingState>({
      day: true,
      tasks: true,
      calendar_entries: true,
      routines: true,
      brain_dumps: true,
      push_notifications: true,
      messages: true,
    });
  const [error, setError] = createSignal<Error | undefined>(undefined);
  const [isConnected, setIsConnected] = createSignal(false);
  const [isOutOfSync, setIsOutOfSync] = createSignal(false);
  const [notifications, setNotifications] = createSignal<PushNotification[]>(
    [],
  );
  const [notificationsLoading, setNotificationsLoading] = createSignal(false);
  const [messages, setMessages] = createSignal<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = createSignal(false);
  const [lastProcessedTimestamp, setLastProcessedTimestamp] = createSignal<
    string | null
  >(null);
  const [lastChangeStreamId, setLastChangeStreamId] = createSignal<
    string | null
  >(null);
  const [debugEvents, setDebugEvents] = createSignal<StreamingDebugEvent[]>([]);

  let debugEventSeq = 0;

  const routines = createMemo(() => {
    const context = dayContextStore.data as DayContextWithRoutines | undefined;
    return context?.routines ?? [];
  });

  let syncDebounceTimeout: number | null = null;
  let isMounted = false;
  let wsClient: WsClient<DomainEventEnvelope> | null = null;
  let fullSyncBaseContext: DayContextWithRoutines | undefined = undefined;
  let nowInterval: number | null = null;

  type BrainDumpWithOptionalId = Omit<BrainDump, "id"> & {
    id?: string | null;
  };

  const hasNonEmptyId = <T extends { id?: string | null }>(
    item: T,
  ): item is T & { id: string } =>
    typeof item.id === "string" && item.id.length > 0;

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

  const dedupeAlarms = (items: Alarm[]): Alarm[] => {
    const deduped: Alarm[] = [];
    items.forEach((alarm) => {
      if (!deduped.some((existing) => isSameAlarm(existing, alarm))) {
        deduped.push(alarm);
      }
    });
    return deduped;
  };

  const DAY_CONTEXT_PARTS: DayContextPartKey[] = [
    "day",
    "tasks",
    "calendar_entries",
    "routines",
    "brain_dumps",
    "push_notifications",
    "messages",
  ];

  const setLoadingForParts = (parts: DayContextPartKey[], loading: boolean) => {
    parts.forEach((part) => {
      setDayContextLoading(part, loading);
    });
  };

  const getPartsFromPartialContext = (
    partial: PartialDayContext,
  ): DayContextPartKey[] => {
    const parts: DayContextPartKey[] = [];
    if (partial.day) parts.push("day");
    if (partial.tasks) parts.push("tasks");
    if (partial.calendar_entries) parts.push("calendar_entries");
    if (partial.routines) parts.push("routines");
    if (partial.brain_dumps) parts.push("brain_dumps");
    if (partial.push_notifications) parts.push("push_notifications");
    if (partial.messages) parts.push("messages");
    return parts;
  };

  const buildEmptyDayContext = (currentDay: Day): DayContextWithRoutines => ({
    day: currentDay,
    tasks: [],
    calendar_entries: [],
    routines: [],
    brain_dumps: [],
    push_notifications: [],
    messages: [],
  });

  const createDebugEventId = (): string => {
    debugEventSeq += 1;
    return `${Date.now()}-${debugEventSeq}`;
  };

  const appendDebugEvent = (entry: Omit<StreamingDebugEvent, "id">) => {
    const nextEntry: StreamingDebugEvent = {
      id: createDebugEventId(),
      ...entry,
    };
    setDebugEvents((prev) => {
      const next = [nextEntry, ...prev];
      return next.length > 200 ? next.slice(0, 200) : next;
    });
  };

  const clearDebugEvents = () => {
    setDebugEvents([]);
  };

  const summarizeSyncResponse = (message: SyncResponseMessage) => {
    const dayContext = message.day_context;
    const partialContext = message.partial_context;
    return {
      hasDayContext: Boolean(dayContext),
      partialKey: message.partial_key ?? null,
      hasPartialContext: Boolean(partialContext),
      changesCount: message.changes?.length ?? 0,
      dayContextSummary: dayContext
        ? {
            tasks: dayContext.tasks?.length ?? 0,
            calendarEntries: dayContext.calendar_entries?.length ?? 0,
            events: dayContext.calendar_entries?.length ?? 0,
            routines:
              (dayContext as DayContextWithRoutines).routines?.length ?? 0,
          }
        : undefined,
      partialContextSummary: partialContext
        ? {
            tasks: partialContext.tasks?.length ?? 0,
            calendarEntries: partialContext.calendar_entries?.length ?? 0,
            routines: partialContext.routines?.length ?? 0,
            brainDumps: partialContext.brain_dumps?.length ?? 0,
            pushNotifications: partialContext.push_notifications?.length ?? 0,
            hasDay: Boolean(partialContext.day),
          }
        : undefined,
      syncComplete: message.sync_complete ?? null,
      lastAuditLogTimestamp: message.last_audit_log_timestamp ?? null,
      lastChangeStreamId: message.last_change_stream_id ?? null,
    };
  };

  const logDebugEvent = (
    direction: StreamingDebugEvent["direction"],
    label: string,
    payload?: unknown,
  ) => {
    appendDebugEvent({
      timestamp: new Date().toISOString(),
      direction,
      label,
      payload,
    });
  };

  // Keep a lightweight clock for time-based derived values (e.g. filtering
  // alarms that have already passed). This avoids relying on websocket updates
  // for purely "time moved forward" changes.
  const [now, setNow] = createSignal(new Date());

  // Derived values from the store
  const dayContext = createMemo(() => dayContextStore.data);
  const tasks = createMemo(() => dayContextStore.data?.tasks ?? []);
  const isPartLoading = (part: DayContextPartKey): boolean =>
    dayContextLoading[part];
  const shouldHideEvent = (
    status?: import("@/types/api").CalendarEntryAttendanceStatus | null,
  ): boolean => status === "DIDNT_HAPPEN" || status === "NOT_GOING";

  const events = createMemo(() =>
    (dayContextStore.data?.calendar_entries ?? []).filter(
      (event) => !shouldHideEvent(event.attendance_status),
    ),
  );
  const reminders = createMemo(() =>
    (tasks() ?? []).filter((t) => t.type === "REMINDER"),
  );
  const alarms = createMemo(() => {
    const context = dayContextStore.data;
    const all = (context?.day?.alarms || []) as Alarm[];
    const dayDate = (context?.day as { date?: string } | undefined)?.date;

    // Touch the clock signal so this memo recomputes as time passes.
    const nowMs = now().getTime();
    const graceMs = 60_000; // avoid flicker around the exact minute boundary

    const getEffectiveAlarmTimeMs = (alarm: Alarm): number | null => {
      const status = (alarm.status ?? "ACTIVE") as AlarmStatus;

      // Snoozed alarms should be evaluated by their snooze time.
      if (status === "SNOOZED" && alarm.snoozed_until) {
        const d = new Date(alarm.snoozed_until);
        const t = d.getTime();
        return Number.isFinite(t) ? t : null;
      }

      // Prefer the server-provided datetime if present.
      if (alarm.datetime) {
        const d = new Date(alarm.datetime);
        const t = d.getTime();
        return Number.isFinite(t) ? t : null;
      }

      // Fall back to combining the day date with the alarm time (local time).
      if (dayDate && alarm.time) {
        const d = new Date(`${dayDate}T${alarm.time}`);
        const t = d.getTime();
        return Number.isFinite(t) ? t : null;
      }

      return null;
    };

    return all.filter((alarm) => {
      const status = (alarm.status ?? "ACTIVE") as AlarmStatus;

      // Always hide cancelled alarms on the main /me/today experience.
      if (status === "CANCELLED") return false;

      // Always keep currently-triggered alarms so overlays/kiosk can react.
      if (status === "TRIGGERED") return true;

      // Hide alarms that are already in the past (missed/outdated).
      const effectiveMs = getEffectiveAlarmTimeMs(alarm);
      if (effectiveMs === null) return true; // if we can't evaluate, keep visible
      return effectiveMs + graceMs >= nowMs;
    });
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
    return normalizeBrainDumps(
      (
        dayContextStore.data as
          | { brain_dumps?: BrainDumpWithOptionalId[] }
          | undefined
      )?.brain_dumps,
    );
  });
  const day = createMemo<Day | undefined>(() => {
    const currentDay = dayContextStore.data?.day;
    if (!currentDay) return undefined;
    return {
      ...currentDay,
      alarms: alarms(),
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
        logDebugEvent("state", "socket_open");
        requestFullSync();
      },
      onClose: () => {
        setIsConnected(false);
        logDebugEvent("state", "socket_closed");
      },
      onError: (err) => {
        console.error("StreamingDataProvider: WebSocket error:", err);
        setError(new Error("Connection error occurred"));
        setIsConnected(false);
        logDebugEvent("error", "socket_error", { message: String(err) });
      },
      onMessage: async (message) => {
        if (message.type === "connection_ack") {
          const ack = message as ConnectionAckMessage;
          logDebugEvent("in", "connection_ack", { user_id: ack.user_id });
          console.log(
            "StreamingDataProvider: Connection acknowledged for user:",
            ack.user_id,
          );
        } else if (message.type === "sync_response") {
          logDebugEvent(
            "in",
            "sync_response",
            summarizeSyncResponse(message as SyncResponseMessage),
          );
          await handleSyncResponse(message as SyncResponseMessage);
        } else if (message.type === "audit_log_event") {
          logDebugEvent("in", "audit_log_event", {
            hasAuditLog: Boolean((message as AuditLogEventMessage).audit_log),
          });
          // Deprecated: This handler is kept for backward compatibility
          // The backend now sends sync_response messages for real-time updates
          await handleAuditLogEvent(message as AuditLogEventMessage);
        } else if (message.type === "error") {
          const errorMsg = message as ErrorMessage;
          setError(new Error(errorMsg.message || "Unknown error"));
          logDebugEvent("error", "server_error", {
            code: errorMsg.code,
            message: errorMsg.message,
          });
          console.error(
            "StreamingDataProvider: WebSocket error:",
            errorMsg.code,
            errorMsg.message,
          );
        } else if (message.type) {
          logDebugEvent("in", `message:${message.type}`, message);
        }
      },
    });

    return wsClient;
  };

  // Connect to WebSocket
  const connectWebSocket = () => {
    setIsConnected(false);
    setError(undefined);
    logDebugEvent("state", "connect");
    getOrCreateWsClient()?.connect();
  };

  // Request full sync
  const requestFullSync = () => {
    fullSyncBaseContext = dayContextStore.data;
    const request: SyncRequestMessage = {
      type: "sync_request",
      since_timestamp: null,
      partial_keys: DAY_CONTEXT_PARTS,
    };
    const sent = getOrCreateWsClient()?.sendJson(request) ?? false;
    logDebugEvent("out", "sync_request", {
      since_timestamp: request.since_timestamp,
      since_change_stream_id: request.since_change_stream_id ?? null,
      partial_keys: request.partial_keys ?? null,
      sent,
    });
    if (sent) {
      setIsLoading(true);
      setLoadingForParts(request.partial_keys ?? DAY_CONTEXT_PARTS, true);
    }
  };

  // Request incremental sync
  const requestIncrementalSync = (sinceTimestamp: string) => {
    const request: SyncRequestMessage = {
      type: "sync_request",
      since_timestamp: sinceTimestamp ?? null,
      since_change_stream_id: lastChangeStreamId(),
    };
    const sent = getOrCreateWsClient()?.sendJson(request) ?? false;
    logDebugEvent("out", "sync_request", {
      since_timestamp: request.since_timestamp,
      since_change_stream_id: request.since_change_stream_id ?? null,
      sent,
    });
  };

  const mergePartialContext = (
    current: DayContextWithRoutines,
    partial: PartialDayContext,
  ): DayContextWithRoutines => {
    let next = { ...current };
    if (partial.day) {
      next = { ...next, day: partial.day };
    }
    if (partial.tasks) {
      next = { ...next, tasks: partial.tasks };
    }
    if (partial.calendar_entries) {
      next = { ...next, calendar_entries: partial.calendar_entries };
    }
    if (partial.routines) {
      next = { ...next, routines: partial.routines };
    }
    if (partial.brain_dumps) {
      next = {
        ...next,
        brain_dumps: partial.brain_dumps,
      };
    }
    if (partial.push_notifications) {
      next = { ...next, push_notifications: partial.push_notifications };
    }
    if (partial.messages) {
      next = { ...next, messages: partial.messages };
    }
    return next;
  };

  const applyPartialContext = (partial: PartialDayContext): boolean => {
    let didUpdate = false;
    setDayContextStore((current) => {
      if (!current.data) {
        if (!partial.day) {
          logDebugEvent("state", "partial_sync_skipped", {
            reason: "missing_day",
          });
          return current;
        }
        const initial = buildEmptyDayContext(partial.day);
        didUpdate = true;
        return { data: mergePartialContext(initial, partial) };
      }
      didUpdate = true;
      return { data: mergePartialContext(current.data, partial) };
    });
    return didUpdate;
  };

  // Handle sync response
  const handleSyncResponse = async (message: SyncResponseMessage) => {
    if (message.partial_context) {
      const previousContext = dayContextStore.data;
      const didApplyChanges = applyPartialContext(message.partial_context);
      if (didApplyChanges) {
        const partsToMark =
          message.partial_key != null
            ? [message.partial_key]
            : getPartsFromPartialContext(message.partial_context);
        if (partsToMark.length > 0) {
          setLoadingForParts(partsToMark, false);
        }
      }
      logDebugEvent("state", "apply_partial_context", {
        partialKey: message.partial_key ?? null,
        didApplyChanges,
      });
      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
      if (message.last_change_stream_id) {
        setLastChangeStreamId(message.last_change_stream_id);
      }
      if (message.sync_complete) {
        setIsLoading(false);
        setLoadingForParts(DAY_CONTEXT_PARTS, false);
        setIsOutOfSync(false);
        void refreshAuxiliaryData();
        const baselineContext = fullSyncBaseContext ?? previousContext;
        fullSyncBaseContext = undefined;
        if (isOnMeRoute() && baselineContext) {
          const completedCount = countCompletedTasksFromFullSync(
            baselineContext.tasks ?? [],
            dayContextStore.data?.tasks ?? [],
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
      }
      return;
    }

    if (message.day_context) {
      setIsLoading(false);
      setLoadingForParts(DAY_CONTEXT_PARTS, false);
      fullSyncBaseContext = undefined;
      const previousContext = dayContextStore.data;
      // Full context - replace store
      setDayContextStore({ data: message.day_context });

      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
      if (message.last_change_stream_id) {
        setLastChangeStreamId(message.last_change_stream_id);
      }
      setIsOutOfSync(false);

      void refreshAuxiliaryData();

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
      logDebugEvent("state", "apply_changes", {
        changesCount: message.changes.length,
        didApplyChanges,
      });
      if (message.last_audit_log_timestamp) {
        setLastProcessedTimestamp(message.last_audit_log_timestamp);
      }
      if (message.last_change_stream_id) {
        setLastChangeStreamId(message.last_change_stream_id);
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
      logDebugEvent("state", "out_of_sync_detected", {
        occurredAt,
        lastProcessed: lastTimestamp,
      });
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
        untrack(() => requestIncrementalSync(timestampToUse));
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

  const rescheduleTask = async (
    task: Task,
    scheduledDate: string,
  ): Promise<void> => {
    if (!task.id) {
      throw new Error("Task id is missing");
    }

    const previousTasks = tasks();
    const updatedTasks = previousTasks.filter((t) => t.id !== task.id);
    setDayContextStore((current) => {
      if (!current.data) return current;
      return { data: { ...current.data, tasks: updatedTasks } };
    });

    try {
      const updatedTask = await taskAPI.rescheduleTask(task.id, scheduledDate);
      const currentDay = day();
      if (currentDay?.date === updatedTask.scheduled_date) {
        addTaskLocally(updatedTask);
      }
    } catch (error) {
      setDayContextStore((current) => {
        if (!current.data) return current;
        return { data: { ...current.data, tasks: previousTasks } };
      });
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

  const updateAlarmsLocally = (updatedAlarms: Alarm[]) => {
    setDayContextStore((current) => {
      if (!current.data) return current;
      const dedupedAlarms = dedupeAlarms(updatedAlarms);
      const nextDay = current.data.day
        ? { ...current.data.day, alarms: dedupedAlarms }
        : current.data.day;
      return {
        data: {
          ...current.data,
          alarms: dedupedAlarms,
          day: nextDay,
        },
      };
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
      if (!current.data) return current;
      const updated = {
        data: {
          ...current.data,
          brain_dumps: updatedItems,
        },
      };
      return updated;
    });
  };

  const refreshAuxiliaryData = async () => {
    const context = dayContextStore.data;
    const normalized = normalizeBrainDumps(
      (
        context as { brain_dumps?: BrainDumpWithOptionalId[] } | undefined
      )?.brain_dumps,
    );
    updateBrainDumpsLocally(normalized);
    setNotifications(context?.push_notifications ?? []);
    setMessages(context?.messages ?? []);
  };

  const addReminder = async (name: string): Promise<void> => {
    const currentDay = day();
    if (!currentDay?.date) return;
    const created = await taskAPI.createAdhocTask({
      scheduled_date: currentDay.date,
      name,
      category: "PLANNING",
      type: "REMINDER",
    });
    addTaskLocally(created);
  };

  const updateReminderStatus = async (
    reminder: Task,
    status: TaskStatus,
  ): Promise<void> => {
    await setTaskStatus(reminder, status);
  };

  const removeReminder = async (reminderId: string): Promise<void> => {
    const previousTasks = tasks();
    const updatedTasks = previousTasks.filter((t) => t.id !== reminderId);
    setDayContextStore((current) => {
      if (!current.data) return current;
      return { data: { ...current.data, tasks: updatedTasks } };
    });
    try {
      await taskAPI.deleteTask(reminderId);
    } catch (error) {
      setDayContextStore((current) => {
        if (!current.data) return current;
        return { data: { ...current.data, tasks: previousTasks } };
      });
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
    const existing = alarms() ?? [];
    if (existing.some((alarm) => isSameAlarm(alarm, created))) {
      updateAlarmLocally(created);
      return;
    }
    updateAlarmsLocally([...existing, created]);
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

  const updateEventLocally = (updatedEvent: Event) => {
    setDayContextStore((current) => {
      if (!current.data) return current;
      const next = (current.data.calendar_entries ?? []).map((e) =>
        e.id === updatedEvent.id ? updatedEvent : e,
      );
      return { data: { ...current.data, calendar_entries: next } };
    });
  };

  const updateEventAttendanceStatus = async (
    event: Event,
    status: import("@/types/api").CalendarEntryAttendanceStatus | null,
  ): Promise<void> => {
    if (!event.id) {
      throw new Error("Event id is missing");
    }

    const previous = event;
    updateEventLocally({ ...event, attendance_status: status });

    try {
      const updated = await calendarEntryAPI.update(event.id, {
        attendance_status: status,
      });
      updateEventLocally(updated);
    } catch (error) {
      updateEventLocally(previous);
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
      setNotifications(dayContextStore.data?.push_notifications ?? []);
    } catch (err) {
      console.error("StreamingDataProvider: Failed to load notifications", err);
    } finally {
      setNotificationsLoading(false);
    }
  };

  const loadMessages = async () => {
    if (messagesLoading()) {
      return;
    }
    setMessagesLoading(true);
    try {
      setMessages(dayContextStore.data?.messages ?? []);
    } catch (err) {
      console.error("StreamingDataProvider: Failed to load messages", err);
    } finally {
      setMessagesLoading(false);
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

    // Keep a "now" signal fresh for relative time UI. Avoid scheduling an
    // interval in the test environment because fake-timer test suites often
    // use runAllTimers(), which would loop indefinitely with intervals.
    if (typeof window !== "undefined" && import.meta.env.MODE !== "test") {
      nowInterval = window.setInterval(() => {
        setNow(new Date());
      }, 30000);
    }
  });

  // Cleanup on unmount
  onCleanup(() => {
    // Set isMounted to false first to prevent reconnection attempts
    isMounted = false;

    if (nowInterval) {
      clearInterval(nowInterval);
      nowInterval = null;
    }
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
    messages,
    day,
    routines,
    isLoading,
    isPartLoading,
    notificationsLoading,
    messagesLoading,
    error,
    isConnected,
    isOutOfSync,
    lastProcessedTimestamp,
    lastChangeStreamId,
    debugEvents,
    clearDebugEvents,
    sync,
    syncIncremental,
    setTaskStatus,
    snoozeTask,
    rescheduleTask,
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
    loadMessages,
    updateEventAttendanceStatus,
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
