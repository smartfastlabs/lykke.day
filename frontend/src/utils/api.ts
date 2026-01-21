import { globalNotifications } from "@/providers/notifications";
import {
  Task,
  DayContext,
  Day,
  DayTemplate,
  TimeBlockDefinition,
  Calendar,
  CalendarEntrySeries,
  TaskDefinition,
  Routine,
  PushSubscription,
  TaskSchedule,
  RecurrenceSchedule,
  SystemTemplate,
  TemplateDetail,
  TemplateOverride,
  TemplatePreview,
} from "@/types/api";
import type { CurrentUser, UserProfileUpdate } from "@/types/api/user";
import type {
  ApiResponse,
  ApiError,
  PaginatedResponse,
} from "@/types/api/utils";

// Custom error class for API errors
export class ApiRequestError extends Error {
  public status: number;
  public detail?: string;
  
  constructor(
    message: string,
    status: number,
    detail?: string
  ) {
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
  options: FetchOptions = {}
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
  options: FetchOptions = {}
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

export const taskAPI = {
  setTaskStatus: (task: Task, status: string): Promise<Task> =>
    fetchData<Task>(`/api/tasks/${task.id}/actions`, {
      method: "POST",
      body: JSON.stringify({ type: status }),
    }),
};

export const reminderAPI = {
  addReminder: (name: string): Promise<DayContext> => {
    // The endpoint expects name as a query parameter
    const params = new URLSearchParams({ name });
    return fetchData<DayContext>(`/api/me/today/reminders?${params.toString()}`, {
      method: "POST",
    });
  },

  updateReminderStatus: (reminderId: string, status: string): Promise<DayContext> => {
    const params = new URLSearchParams({ status });
    return fetchData<DayContext>(
      `/api/me/today/reminders/${reminderId}?${params.toString()}`,
      {
        method: "PATCH",
      }
    );
  },

  removeReminder: (reminderId: string): Promise<DayContext> =>
    fetchData<DayContext>(`/api/me/today/reminders/${reminderId}`, {
      method: "DELETE",
    }),
};

export const brainDumpAPI = {
  addItem: (text: string): Promise<DayContext> => {
    const params = new URLSearchParams({ text });
    return fetchData<DayContext>(`/api/me/today/brain-dump?${params.toString()}`, {
      method: "POST",
    });
  },

  updateItemStatus: (itemId: string, status: string): Promise<DayContext> => {
    const params = new URLSearchParams({ status });
    return fetchData<DayContext>(
      `/api/me/today/brain-dump/${itemId}?${params.toString()}`,
      {
        method: "PATCH",
      }
    );
  },

  removeItem: (itemId: string): Promise<DayContext> =>
    fetchData<DayContext>(`/api/me/today/brain-dump/${itemId}`, {
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
    }
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
        errorData.detail
      );
    }
  },

  register: async (email: string, password: string): Promise<unknown> => {
    return fetchData("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      suppressAuthRedirect: true,
    });
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

  forgotPassword: async (email: string): Promise<void> => {
    const response = await fetch("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
      headers: DEFAULT_HEADERS,
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiRequestError(
        (errorData as ApiError).detail || "Unable to request password reset",
        response.status,
        (errorData as ApiError).detail
      );
    }
  },

  resetPassword: async (token: string, password: string): Promise<void> => {
    const response = await fetch("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
      headers: DEFAULT_HEADERS,
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiRequestError(
        (errorData as ApiError).detail || "Unable to reset password",
        response.status,
        (errorData as ApiError).detail
      );
    }
  },

  updateProfile: async (payload: UserProfileUpdate): Promise<CurrentUser> => {
    return fetchData<CurrentUser>("/api/me", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
};

export const pushAPI = {
  getSubscriptions: async (): Promise<PushSubscription[]> => {
    const data = await fetchData<PaginatedResponse<PushSubscription>>(
      "/api/push/subscriptions/",
      {
        method: "POST",
        body: JSON.stringify({ limit: 1000, offset: 0 }),
      }
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
  addRoutine: (
    dayTemplateId: string,
    routineId: string
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(`/api/day-templates/${dayTemplateId}/routines`, {
      method: "POST",
      body: JSON.stringify({ routine_id: routineId }),
    }),
  removeRoutine: (
    dayTemplateId: string,
    routineId: string
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(
      `/api/day-templates/${dayTemplateId}/routines/${routineId}`,
      {
        method: "DELETE",
      }
    ),
  addTimeBlock: (
    dayTemplateId: string,
    timeBlockDefinitionId: string,
    startTime: string,
    endTime: string
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
    startTime: string
  ): Promise<DayTemplate> =>
    fetchData<DayTemplate>(
      `/api/day-templates/${dayTemplateId}/time-blocks/${timeBlockDefinitionId}/${startTime}`,
      {
        method: "DELETE",
      }
    ),
};

export const templateAPI = {
  getSystemTemplates: (): Promise<SystemTemplate[]> =>
    fetchData<SystemTemplate[]>("/api/templates/system"),
  getOverrides: (): Promise<TemplateOverride[]> =>
    fetchData<TemplateOverride[]>("/api/templates/overrides"),
  getDetail: (usecase: string): Promise<TemplateDetail> =>
    fetchData<TemplateDetail>(`/api/templates/${encodeURIComponent(usecase)}`),
  create: (payload: {
    usecase: string;
    key: string;
    name?: string | null;
    description?: string | null;
    content: string;
  }): Promise<TemplateOverride> =>
    fetchData<TemplateOverride>("/api/templates/create", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  update: (payload: {
    id: string;
    name?: string | null;
    description?: string | null;
    content?: string | null;
  }): Promise<TemplateOverride> =>
    fetchData<TemplateOverride>(`/api/templates/${payload.id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: payload.name ?? undefined,
        description: payload.description ?? undefined,
        content: payload.content ?? undefined,
      }),
    }),
  delete: (id: string): Promise<void> =>
    fetchData<void>(`/api/templates/${id}`, { method: "DELETE" }),
  preview: (usecase: string): Promise<TemplatePreview> =>
    fetchData<TemplatePreview>("/api/templates/preview", {
      method: "POST",
      body: JSON.stringify({ usecase }),
    }),
};

export const taskDefinitionAPI = {
  ...createCrudMethods<TaskDefinition>("task-definitions"),
};

export const timeBlockDefinitionAPI = {
  ...createCrudMethods<TimeBlockDefinition>("time-block-definitions"),
};

export const routineAPI = {
  setRoutineAction: (routineId: string, action: string): Promise<Task[]> =>
    fetchData<Task[]>(`/api/routines/${routineId}/actions`, {
      method: "POST",
      body: JSON.stringify({ type: action }),
    }),
  ...createCrudMethods<Routine>("routines"),
  addTask: (
    routineId: string,
    payload: {
      task_definition_id: string;
      name?: string | null;
      schedule?: TaskSchedule | null;
      task_schedule?: RecurrenceSchedule | null;
    }
  ): Promise<Routine> =>
    fetchData<Routine>(`/api/routines/${routineId}/tasks`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTask: (
    routineId: string,
    routineTaskId: string,
    payload: { name?: string | null; schedule?: TaskSchedule | null; task_schedule?: RecurrenceSchedule | null }
  ): Promise<Routine> =>
    fetchData<Routine>(`/api/routines/${routineId}/tasks/${routineTaskId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  removeTask: (routineId: string, routineTaskId: string): Promise<Routine> =>
    fetchData<Routine>(`/api/routines/${routineId}/tasks/${routineTaskId}`, {
      method: "DELETE",
    }),
};

export const calendarAPI = {
  get: (id: string): Promise<Calendar> => fetchData<Calendar>(`/api/calendars/${id}`),

  getAll: async (): Promise<Calendar[]> => {
    const data = await fetchData<PaginatedResponse<Calendar>>(
      `/api/calendars/`,
      {
        method: "POST",
        body: JSON.stringify({ limit: 1000, offset: 0 }),
      }
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
      }
    );
    return data.items;
  },

  update: (item: CalendarEntrySeries): Promise<CalendarEntrySeries> =>
    fetchData<CalendarEntrySeries>(`/api/calendar-entry-series/${item.id}`, {
      method: "PUT",
      body: JSON.stringify(item),
    }),

  searchByCalendar: async (calendarId: string): Promise<CalendarEntrySeries[]> => {
    const data = await fetchData<PaginatedResponse<CalendarEntrySeries>>(
      "/api/calendar-entry-series/",
      {
        method: "POST",
        body: JSON.stringify({ 
          limit: 1000, 
          offset: 0,
          filters: { calendar_id: calendarId }
        }),
      }
    );
    return data.items;
  },
};

export const marketingAPI = {
  requestEarlyAccess: (email: string): Promise<void> =>
    fetchData<void>("/api/early-access", {
      method: "POST",
      body: JSON.stringify({ email }),
      suppressAuthRedirect: true,
      suppressError: true,
    }),
};
