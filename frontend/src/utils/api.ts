import { globalNotifications } from "@/providers/notifications";
import {
  Task,
  Day,
  DayTemplate,
  TimeBlockDefinition,
  Calendar,
  CalendarEntrySeries,
  TaskDefinition,
  TaskDefinitionCreate,
  RoutineDefinition,
  PushSubscription,
  ActionType,
  TaskStatus,
  TimeWindow,
  RecurrenceSchedule,
  UseCaseConfig,
  NotificationUseCaseConfig,
  MessagingUseCaseConfig,
  LLMRunResultSnapshot,
  Alarm,
  BrainDump,
  PushNotification,
  Factoid,
  Tactic,
  Trigger,
} from "@/types/api";
import type {
  BasePersonalityOption,
  CurrentUser,
  UserProfileUpdate,
} from "@/types/api/user";
import type {
  ApiResponse,
  ApiError,
  PaginatedResponse,
} from "@/types/api/utils";

// Custom error class for API errors
export class ApiRequestError extends Error {
  public status: number;
  public detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = detail;
  }
}

interface FetchOptions extends Omit<RequestInit, "headers"> {
  suppressError?: boolean;
  suppressAuthRedirect?: boolean;
  headers?: Record<string, string>;
}

const DEFAULT_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
};

async function fetchJSON<T>(
  url: string,
  options: FetchOptions = {},
): Promise<ApiResponse<T>> {
  const {
    suppressError = false,
    suppressAuthRedirect = false,
    headers = {},
    ...fetchOptions
  } = options;

  const mergedHeaders = { ...DEFAULT_HEADERS, ...headers };

  const response = await fetch(url, {
    ...fetchOptions,
    headers: mergedHeaders,
    credentials: "include",
  });

  // Handle 401 Unauthorized
  if (response.status === 401) {
    if (!suppressError) {
      globalNotifications.addError("Not logged in");
    }
    if (
      !suppressAuthRedirect &&
      !["/login", "/register"].includes(window.location.pathname)
    ) {
      window.location.href = "/login";
    }
    throw new ApiRequestError("Unauthorized", 401);
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return {
      data: undefined as T,
      status: response.status,
      ok: true,
    };
  }

  const body = await response.json();

  if (!response.ok) {
    const errorBody = body as ApiError;
    const errorMessage = errorBody.detail || "Unknown error";

    if (!suppressError) {
      globalNotifications.addError(`Error: ${errorMessage}`);
    }

    throw new ApiRequestError(errorMessage, response.status, errorBody.detail);
  }

  return {
    data: body as T,
    status: response.status,
    ok: true,
  };
}

// Helper to extract data from response (throws on error)
async function fetchData<T>(
  url: string,
  options: FetchOptions = {},
): Promise<T> {
  const response = await fetchJSON<T>(url, options);
  return response.data;
}

// --- Generic CRUD Factory ---

interface EntityWithId {
  id?: string | null;
}

function createCrudMethods<T extends EntityWithId>(type: string) {
  return {
    get: (id: string): Promise<T> => fetchData<T>(`/api/${type}/${id}`),

    getAll: async (): Promise<T[]> => {
      const data = await fetchData<PaginatedResponse<T>>(`/api/${type}/`, {
        method: "POST",
        body: JSON.stringify({ limit: 1000, offset: 0 }),
      });
      return data.items;
    },

    create: (item: Omit<T, "id">): Promise<T> =>
      fetchData<T>(`/api/${type}/create`, {
        method: "POST",
        body: JSON.stringify(item),
      }),

    update: (item: T): Promise<T> =>
      fetchData<T>(`/api/${type}/${item.id}`, {
        method: "PUT",
        body: JSON.stringify(item),
      }),

    delete: (id: string): Promise<void> =>
      fetchData<void>(`/api/${type}/${id}`, { method: "DELETE" }),
  };
}

// --- API Modules ---

export type TaskActionPayload = {
  type: ActionType;
  data?: Record<string, string>;
};

export const taskAPI = {
  recordTaskAction: (
    taskId: string,
    action: TaskActionPayload,
  ): Promise<Task> =>
    fetchData<Task>(`/api/tasks/${taskId}/actions`, {
      method: "POST",
      body: JSON.stringify(action),
    }),
  setTaskStatus: (
    task: Task,
    status: ActionType | TaskStatus,
  ): Promise<Task> =>
    task.id
      ? taskAPI.recordTaskAction(task.id, { type: status as ActionType })
      : Promise.reject(new Error("Task id is missing")),
  createAdhocTask: (payload: {
    scheduled_date: string;
    name: string;
    type?: Task["type"];
    category: Task["category"];
    description?: string | null;
    time_window?: TimeWindow | null;
    tags?: Task["tags"];
  }): Promise<Task> =>
    fetchData<Task>("/api/tasks/adhoc", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rescheduleTask: (taskId: string, scheduledDate: string): Promise<Task> =>
    fetchData<Task>(`/api/tasks/${taskId}/reschedule`, {
      method: "POST",
      body: JSON.stringify({ scheduled_date: scheduledDate }),
    }),
  deleteTask: (taskId: string): Promise<void> =>
    fetchData<void>(`/api/tasks/${taskId}`, { method: "DELETE" }),
};

export const tomorrowAPI = {
  ensureScheduled: (): Promise<Day> =>
    fetchData<Day>("/api/me/tomorrow/ensure-scheduled", { method: "POST" }),
  reschedule: (): Promise<Day> =>
    fetchData<Day>("/api/me/tomorrow/reschedule", { method: "PUT" }),
  getDay: (): Promise<Day> => fetchData<Day>("/api/me/tomorrow/day"),
  getCalendarEntries: (): Promise<import("@/types/api").Event[]> =>
    fetchData<import("@/types/api").Event[]>(
      "/api/me/tomorrow/calendar-entries",
    ),
  getTasks: (): Promise<Task[]> => fetchData<Task[]>("/api/me/tomorrow/tasks"),
  getRoutines: (): Promise<import("@/types/api").Routine[]> =>
    fetchData<import("@/types/api").Routine[]>("/api/me/tomorrow/routines"),

  addAlarm: (payload: {
    name?: string;
    time: string;
    alarm_type?: string;
    url?: string;
  }): Promise<Alarm> => {
    const params = new URLSearchParams({ time: payload.time });
    if (payload.name) params.set("name", payload.name);
    if (payload.alarm_type) params.set("alarm_type", payload.alarm_type);
    if (payload.url) params.set("url", payload.url);
    return fetchData<Alarm>(`/api/me/tomorrow/alarms?${params.toString()}`, {
      method: "POST",
    });
  },
  removeAlarm: (payload: {
    name: string;
    time: string;
    alarm_type?: string;
    url?: string;
  }): Promise<Alarm> => {
    const params = new URLSearchParams({
      name: payload.name,
      time: payload.time,
    });
    if (payload.alarm_type) params.set("alarm_type", payload.alarm_type);
    if (payload.url) params.set("url", payload.url);
    return fetchData<Alarm>(`/api/me/tomorrow/alarms?${params.toString()}`, {
      method: "DELETE",
    });
  },
  updateAlarmStatus: (payload: {
    alarm_id: string;
    status: string;
    snoozed_until?: string | null;
  }): Promise<Alarm> => {
    const params = new URLSearchParams({ status: payload.status });
    if (payload.snoozed_until)
      params.set("snoozed_until", payload.snoozed_until);
    return fetchData<Alarm>(
      `/api/me/tomorrow/alarms/${payload.alarm_id}?${params.toString()}`,
      { method: "PATCH" },
    );
  },
};

export const alarmAPI = {
  addAlarm: (payload: {
    name?: string;
    time: string;
    alarm_type?: string;
    url?: string;
  }): Promise<Alarm> => {
    const params = new URLSearchParams({ time: payload.time });
    if (payload.name) {
      params.set("name", payload.name);
    }
    if (payload.alarm_type) {
      params.set("alarm_type", payload.alarm_type);
    }
    if (payload.url) {
      params.set("url", payload.url);
    }
    return fetchData<Alarm>(`/api/me/today/alarms?${params.toString()}`, {
      method: "POST",
    });
  },
  removeAlarm: (payload: {
    name: string;
    time: string;
    alarm_type?: string;
    url?: string;
  }): Promise<Alarm> => {
    const params = new URLSearchParams({
      name: payload.name,
      time: payload.time,
    });
    if (payload.alarm_type) {
      params.set("alarm_type", payload.alarm_type);
    }
    if (payload.url) {
      params.set("url", payload.url);
    }
    return fetchData<Alarm>(`/api/me/today/alarms?${params.toString()}`, {
      method: "DELETE",
    });
  },
  updateAlarmStatus: (payload: {
    alarm_id: string;
    status: string;
    snoozed_until?: string | null;
  }): Promise<Alarm> => {
    const params = new URLSearchParams({ status: payload.status });
    if (payload.snoozed_until) {
      params.set("snoozed_until", payload.snoozed_until);
    }
    return fetchData<Alarm>(
      `/api/me/today/alarms/${payload.alarm_id}?${params.toString()}`,
      {
        method: "PATCH",
      },
    );
  },
};

export const brainDumpAPI = {
  getToday: async (): Promise<BrainDump[]> => {
    const now = new Date();
    const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(
      2,
      "0",
    )}-${String(now.getDate()).padStart(2, "0")}`;

    const data = await fetchData<PaginatedResponse<BrainDump>>(
      "/api/brain-dump/",
      {
        method: "POST",
        body: JSON.stringify({
          limit: 1000,
          offset: 0,
          filters: {
            date,
            order_by: "created_at",
            order_by_desc: true,
          },
        }),
      },
    );
    return data.items;
  },
  get: (id: string): Promise<BrainDump> =>
    fetchData<BrainDump>(`/api/brain-dump/${id}`),
  addItem: (text: string): Promise<BrainDump> => {
    const params = new URLSearchParams({ text });
    return fetchData<BrainDump>(
      `/api/me/today/brain-dump?${params.toString()}`,
      {
        method: "POST",
      },
    );
  },

  updateItemStatus: (itemId: string, status: string): Promise<BrainDump> => {
    const params = new URLSearchParams({ status });
    return fetchData<BrainDump>(
      `/api/me/today/brain-dump/${itemId}?${params.toString()}`,
      {
        method: "PATCH",
      },
    );
  },

  removeItem: (itemId: string): Promise<BrainDump> =>
    fetchData<BrainDump>(`/api/me/today/brain-dump/${itemId}`, {
      method: "DELETE",
    }),
};

export const dayAPI = {
  updateDay: (
    dayId: string,
    payload: {
      starts_at?: string | null;
      ends_at?: string | null;
      high_level_plan?: {
        title?: string | null;
        text?: string | null;
        intentions?: string[];
      } | null;
    },
  ): Promise<Day> =>
    fetchData<Day>(`/api/days/${dayId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};

export const authAPI = {
  me: async (): Promise<CurrentUser | null> => {
    try {
      return await fetchData<CurrentUser>("/api/me", {
        suppressAuthRedirect: true,
        suppressError: true,
      });
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        return null;
      }
      throw error;
    }
  },

  login: async (email: string, password: string): Promise<void> => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch("/api/auth/login", {
      method: "POST",
      body: formData,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiRequestError(
        errorData.detail || "Login failed",
        response.status,
        errorData.detail,
      );
    }
  },

  register: async (
    email: string,
    password: string,
    phone_number: string,
  ): Promise<unknown> => {
    return fetchData("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, phone_number }),
      suppressAuthRedirect: true,
    });
  },

  requestSmsCode: async (phone_number: string): Promise<void> => {
    await fetchData<{ status: string }>("/api/auth/sms/request", {
      method: "POST",
      body: JSON.stringify({ phone_number }),
      suppressAuthRedirect: true,
    });
  },

  verifySmsCode: async (phone_number: string, code: string): Promise<void> => {
    const response = await fetch("/api/auth/sms/verify", {
      method: "POST",
      body: JSON.stringify({ phone_number, code }),
      headers: DEFAULT_HEADERS,
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiRequestError(
        (errorData as ApiError).detail || "Invalid or expired code",
        response.status,
        (errorData as ApiError).detail,
      );
    }
  },

  logout: async (): Promise<void> => {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      throw new ApiRequestError("Logout failed", response.status);
    }
  },

  updateProfile: async (payload: UserProfileUpdate): Promise<CurrentUser> => {
    return fetchData<CurrentUser>("/api/me", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
};

export const basePersonalityAPI = {
  list: (): Promise<BasePersonalityOption[]> =>
    fetchData<BasePersonalityOption[]>("/api/me/base-personalities"),
};

export const pushAPI = {
  getSubscriptions: async (): Promise<PushSubscription[]> => {
    const data = await fetchData<PaginatedResponse<PushSubscription>>(
      "/api/push/subscriptions/",
      {
        method: "POST",
        body: JSON.stringify({ limit: 1000, offset: 0 }),
      },
    );
    return data.items;
  },

  get: (id: string): Promise<PushSubscription> =>
    fetchData<PushSubscription>(`/api/push/subscriptions/${id}`),

  update: (subscription: PushSubscription): Promise<PushSubscription> =>
    fetchData<PushSubscription>(`/api/push/subscriptions/${subscription.id}`, {
      method: "PUT",
      body: JSON.stringify({ device_name: subscription.device_name }),
    }),

  deleteSubscription: (id: string): Promise<void> =>
    fetchData<void>(`/api/push/subscriptions/${id}`, { method: "DELETE" }),
};

export const dayTemplateAPI = {
  ...createCrudMethods<DayTemplate>("day-templates"),
  addRoutineDefinition: (
    dayTemplateId: string,
    routineDefinitionId: string,
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(
      `/api/day-templates/${dayTemplateId}/routine-definitions`,
      {
        method: "POST",
        body: JSON.stringify({
          routine_definition_id: routineDefinitionId,
        }),
      },
    ),
  removeRoutineDefinition: (
    dayTemplateId: string,
    routineDefinitionId: string,
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(
      `/api/day-templates/${dayTemplateId}/routine-definitions/${routineDefinitionId}`,
      {
        method: "DELETE",
      },
    ),
  addTimeBlock: (
    dayTemplateId: string,
    timeBlockDefinitionId: string,
    startTime: string,
    endTime: string,
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(`/api/day-templates/${dayTemplateId}/time-blocks`, {
      method: "POST",
      body: JSON.stringify({
        time_block_definition_id: timeBlockDefinitionId,
        start_time: startTime,
        end_time: endTime,
      }),
    }),
  removeTimeBlock: (
    dayTemplateId: string,
    timeBlockDefinitionId: string,
    startTime: string,
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(
      `/api/day-templates/${dayTemplateId}/time-blocks/${timeBlockDefinitionId}/${startTime}`,
      {
        method: "DELETE",
      },
    ),
};

export const taskDefinitionAPI = {
  ...createCrudMethods<TaskDefinition>("task-definitions"),
  create: (item: TaskDefinitionCreate): Promise<TaskDefinition> =>
    fetchData<TaskDefinition>("/api/task-definitions/create", {
      method: "POST",
      body: JSON.stringify(item),
    }),
};

export const timeBlockDefinitionAPI = {
  ...createCrudMethods<TimeBlockDefinition>("time-block-definitions"),
};

export const usecaseConfigAPI = {
  get: (usecase: string): Promise<UseCaseConfig | null> =>
    fetchData<UseCaseConfig | null>(
      `/api/usecase-configs/${encodeURIComponent(usecase)}`,
    ),

  createOrUpdate: (payload: {
    usecase: string;
    config: Record<string, unknown>;
  }): Promise<UseCaseConfig> =>
    fetchData<UseCaseConfig>("/api/usecase-configs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  delete: (id: string): Promise<void> =>
    fetchData<void>(`/api/usecase-configs/${id}`, { method: "DELETE" }),

  // Typed methods for notification usecase
  getNotificationConfig: (): Promise<NotificationUseCaseConfig> =>
    fetchData<NotificationUseCaseConfig>("/api/usecase-configs/notification", {
      suppressError: true, // 404 is expected when no config exists
    }).catch((err) => {
      // If 404, return empty config instead of throwing
      if (err instanceof ApiRequestError && err.status === 404) {
        return { user_amendments: [] } as NotificationUseCaseConfig;
      }
      throw err;
    }),

  updateNotificationConfig: (
    config: NotificationUseCaseConfig,
  ): Promise<NotificationUseCaseConfig> =>
    fetchData<NotificationUseCaseConfig>("/api/usecase-configs/notification", {
      method: "PUT",
      body: JSON.stringify(config),
    }),

  getNotificationLLMSnapshotPreview: (): Promise<LLMRunResultSnapshot | null> =>
    fetchData<LLMRunResultSnapshot | null>(
      "/api/usecase-configs/notification/llm-preview",
      { suppressError: true },
    ).catch((err) => {
      if (err instanceof ApiRequestError && err.status === 404) {
        return null;
      }
      throw err;
    }),

  // Typed methods for morning overview usecase
  getMorningOverviewConfig: (): Promise<NotificationUseCaseConfig> =>
    fetchData<NotificationUseCaseConfig>(
      "/api/usecase-configs/morning_overview",
      {
        suppressError: true, // 404 is expected when no config exists
      },
    ).catch((err) => {
      if (err instanceof ApiRequestError && err.status === 404) {
        return { user_amendments: [] } as NotificationUseCaseConfig;
      }
      throw err;
    }),

  updateMorningOverviewConfig: (
    config: NotificationUseCaseConfig,
  ): Promise<NotificationUseCaseConfig> =>
    fetchData<NotificationUseCaseConfig>(
      "/api/usecase-configs/morning_overview",
      {
        method: "PUT",
        body: JSON.stringify(config),
      },
    ),

  getMorningOverviewLLMSnapshotPreview: (): Promise<LLMRunResultSnapshot | null> =>
    fetchData<LLMRunResultSnapshot | null>(
      "/api/usecase-configs/morning_overview/llm-preview",
      { suppressError: true },
    ).catch((err) => {
      if (err instanceof ApiRequestError && err.status === 404) {
        return null;
      }
      throw err;
    }),

  // Typed methods for messaging usecase
  getMessagingConfig: (): Promise<MessagingUseCaseConfig> =>
    fetchData<MessagingUseCaseConfig>(
      "/api/usecase-configs/process_inbound_sms",
      {
        suppressError: true, // 404 is expected when no config exists
      },
    ).catch((err) => {
      if (err instanceof ApiRequestError && err.status === 404) {
        return {
          user_amendments: [],
          send_acknowledgment: true,
        } as MessagingUseCaseConfig;
      }
      throw err;
    }),

  updateMessagingConfig: (
    config: MessagingUseCaseConfig,
  ): Promise<MessagingUseCaseConfig> =>
    fetchData<MessagingUseCaseConfig>(
      "/api/usecase-configs/process_inbound_sms",
      {
        method: "PUT",
        body: JSON.stringify(config),
      },
    ),

  getMessagingLLMSnapshotPreview: (): Promise<LLMRunResultSnapshot | null> =>
    fetchData<LLMRunResultSnapshot | null>(
      "/api/usecase-configs/process_inbound_sms/llm-preview",
      { suppressError: true },
    ).catch((err) => {
      if (err instanceof ApiRequestError && err.status === 404) {
        return null;
      }
      throw err;
    }),
};

export const routineAPI = {
  setRoutineAction: (
    routineId: string,
    action: TaskActionPayload,
  ): Promise<Task[]> =>
    fetchData<Task[]>(`/api/routines/${routineId}/actions`, {
      method: "POST",
      body: JSON.stringify(action),
    }),
  addToToday: (routineDefinitionId: string): Promise<Task[]> => {
    const params = new URLSearchParams({
      routine_definition_id: routineDefinitionId,
    });
    return fetchData<Task[]>(`/api/me/today/routines?${params.toString()}`, {
      method: "POST",
    });
  },
  addToTomorrow: (routineDefinitionId: string): Promise<Task[]> => {
    const params = new URLSearchParams({
      routine_definition_id: routineDefinitionId,
    });
    return fetchData<Task[]>(`/api/me/tomorrow/routines?${params.toString()}`, {
      method: "POST",
    });
  },
};

export const routineDefinitionAPI = {
  ...createCrudMethods<RoutineDefinition>("routine-definitions"),
  addTask: (
    routineDefinitionId: string,
    payload: {
      task_definition_id: string;
      name?: string | null;
      task_schedule?: RecurrenceSchedule | null;
      time_window?: TimeWindow | null;
    },
  ): Promise<RoutineDefinition> =>
    fetchData<RoutineDefinition>(
      `/api/routine-definitions/${routineDefinitionId}/tasks`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),
  updateTask: (
    routineDefinitionId: string,
    routineDefinitionTaskId: string,
    payload: {
      name?: string | null;
      task_schedule?: RecurrenceSchedule | null;
      time_window?: TimeWindow | null;
    },
  ): Promise<RoutineDefinition> =>
    fetchData<RoutineDefinition>(
      `/api/routine-definitions/${routineDefinitionId}/tasks/${routineDefinitionTaskId}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    ),
  removeTask: (
    routineDefinitionId: string,
    routineDefinitionTaskId: string,
  ): Promise<RoutineDefinition> =>
    fetchData<RoutineDefinition>(
      `/api/routine-definitions/${routineDefinitionId}/tasks/${routineDefinitionTaskId}`,
      {
        method: "DELETE",
      },
    ),
};

export const factoidAPI = {
  ...createCrudMethods<Factoid>("factoids"),
};

export const tacticAPI = {
  ...createCrudMethods<Tactic>("tactics"),
  listDefaults: (): Promise<Omit<Tactic, "id">[]> =>
    fetchData<Omit<Tactic, "id">[]>("/api/tactics/defaults"),
  importDefaults: (): Promise<Tactic[]> =>
    fetchData<Tactic[]>("/api/tactics/import-defaults", { method: "POST" }),
};

export const triggerAPI = {
  ...createCrudMethods<Trigger>("triggers"),
  listDefaults: (): Promise<Omit<Trigger, "id">[]> =>
    fetchData<Omit<Trigger, "id">[]>("/api/triggers/defaults"),
  importDefaults: (): Promise<Trigger[]> =>
    fetchData<Trigger[]>("/api/triggers/import-defaults", { method: "POST" }),
  getTactics: (triggerId: string): Promise<Tactic[]> =>
    fetchData<Tactic[]>(`/api/triggers/${triggerId}/tactics`),
  updateTactics: (triggerId: string, tacticIds: string[]): Promise<Tactic[]> =>
    fetchData<Tactic[]>(`/api/triggers/${triggerId}/tactics`, {
      method: "PUT",
      body: JSON.stringify({ tactic_ids: tacticIds }),
    }),
};

export const notificationAPI = {
  getToday: async (): Promise<PushNotification[]> => {
    const now = new Date();
    const startOfDay = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
    );
    const endOfDay = new Date(startOfDay);
    endOfDay.setDate(startOfDay.getDate() + 1);
    const startInclusive = new Date(startOfDay.getTime() - 1);

    const data = await fetchData<PaginatedResponse<PushNotification>>(
      "/api/push-notifications/",
      {
        method: "POST",
        body: JSON.stringify({
          limit: 1000,
          offset: 0,
          filters: {
            sent_after: startInclusive.toISOString(),
            sent_before: endOfDay.toISOString(),
            order_by: "sent_at",
            order_by_desc: true,
          },
        }),
      },
    );
    return data.items;
  },
  get: (id: string): Promise<PushNotification> =>
    fetchData<PushNotification>(`/api/push-notifications/${id}`),
};

export const calendarAPI = {
  get: (id: string): Promise<Calendar> =>
    fetchData<Calendar>(`/api/calendars/${id}`),

  getAll: async (): Promise<Calendar[]> => {
    const data = await fetchData<PaginatedResponse<Calendar>>(
      `/api/calendars/`,
      {
        method: "POST",
        body: JSON.stringify({ limit: 1000, offset: 0 }),
      },
    );
    return data.items;
  },

  update: (item: Calendar): Promise<Calendar> =>
    fetchData<Calendar>(`/api/calendars/${item.id}`, {
      method: "PUT",
      body: JSON.stringify(item),
    }),

  delete: (id: string): Promise<void> =>
    fetchData<void>(`/api/calendars/${id}`, { method: "DELETE" }),

  subscribe: (id: string): Promise<Calendar> =>
    fetchData<Calendar>(`/api/calendars/${id}/subscribe`, { method: "POST" }),
  unsubscribe: (id: string): Promise<Calendar> =>
    fetchData<Calendar>(`/api/calendars/${id}/subscribe`, { method: "DELETE" }),
  resync: (id: string): Promise<Calendar> =>
    fetchData<Calendar>(`/api/calendars/${id}/resync`, { method: "POST" }),
  resetSubscriptions: (): Promise<Calendar[]> =>
    fetchData<Calendar[]>("/api/calendars/reset-subscriptions", {
      method: "POST",
    }),
};

export const calendarEntrySeriesAPI = {
  get: (id: string): Promise<CalendarEntrySeries> =>
    fetchData<CalendarEntrySeries>(`/api/calendar-entry-series/${id}`),

  getAll: async (): Promise<CalendarEntrySeries[]> => {
    const data = await fetchData<PaginatedResponse<CalendarEntrySeries>>(
      `/api/calendar-entry-series/`,
      {
        method: "POST",
        body: JSON.stringify({ limit: 1000, offset: 0 }),
      },
    );
    return data.items;
  },

  update: (item: CalendarEntrySeries): Promise<CalendarEntrySeries> =>
    fetchData<CalendarEntrySeries>(`/api/calendar-entry-series/${item.id}`, {
      method: "PUT",
      body: JSON.stringify(item),
    }),

  searchByCalendar: async (
    calendarId: string,
  ): Promise<CalendarEntrySeries[]> => {
    const data = await fetchData<PaginatedResponse<CalendarEntrySeries>>(
      "/api/calendar-entry-series/",
      {
        method: "POST",
        body: JSON.stringify({
          limit: 1000,
          offset: 0,
          filters: { calendar_id: calendarId },
        }),
      },
    );
    return data.items;
  },
};

export const calendarEntryAPI = {
  update: (
    id: string,
    patch: Partial<{
      attendance_status:
        | import("@/types/api").CalendarEntryAttendanceStatus
        | null;
      name: string | null;
      status: string | null;
      starts_at: string | null;
      ends_at: string | null;
      frequency: import("@/types/api").TaskFrequency | null;
      category: import("@/types/api").Event["category"] | null;
      calendar_entry_series_id: string | null;
    }>,
  ): Promise<import("@/types/api").Event> =>
    fetchData<import("@/types/api").Event>(`/api/calendar-entries/${id}`, {
      method: "PUT",
      body: JSON.stringify(patch),
    }),
};

export const marketingAPI = {
  requestEarlyAccess: (payload: {
    email?: string;
    phone_number?: string;
  }): Promise<void> =>
    fetchData<void>("/api/early-access", {
      method: "POST",
      body: JSON.stringify(payload),
      suppressAuthRedirect: true,
      suppressError: true,
    }),
};

// --- Admin API ---

export interface DomainEventItem {
  id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  stored_at: string;
}

export interface DomainEventFilters {
  search?: string;
  user_id?: string;
  event_type?: string;
  start_time?: string;
  end_time?: string;
  limit?: number;
  offset?: number;
}

export interface DomainEventListResponse {
  items: DomainEventItem[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export const adminAPI = {
  getDomainEvents: (
    filters: DomainEventFilters = {},
  ): Promise<DomainEventListResponse> => {
    const params = new URLSearchParams();
    if (filters.search) params.set("search", filters.search);
    if (filters.user_id) params.set("user_id", filters.user_id);
    if (filters.event_type) params.set("event_type", filters.event_type);
    if (filters.start_time) params.set("start_time", filters.start_time);
    if (filters.end_time) params.set("end_time", filters.end_time);
    if (filters.limit) params.set("limit", String(filters.limit));
    if (filters.offset) params.set("offset", String(filters.offset));

    return fetchData<DomainEventListResponse>(
      `/api/admin/events?${params.toString()}`,
    );
  },
};
