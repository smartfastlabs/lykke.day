import { globalNotifications } from "@/providers/notifications";
import {
  Event,
  Task,
  Day,
  DayContext,
  DayTemplate,
  TaskDefinition,
  Routine,
  PushSubscription,
  TaskSchedule,
} from "@/types/api";
import type {
  ApiResponse,
  ApiError,
  PaginatedResponse,
} from "@/types/api/utils";

// Custom error class for API errors
export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiRequestError";
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

// Helper for paginated responses
function extractItems<T>(data: T[] | PaginatedResponse<T>): T[] {
  if (Array.isArray(data)) {
    return data;
  }
  return data.items;
}

// --- Generic CRUD Factory ---

interface EntityWithId {
  id?: string;
}

function createCrudMethods<T extends EntityWithId>(type: string) {
  return {
    get: (id: string): Promise<T> => fetchData<T>(`/api/${type}/${id}`),

    getAll: async (): Promise<T[]> => {
      const data = await fetchData<T[] | PaginatedResponse<T>>(`/api/${type}/`);
      return extractItems(data);
    },

    create: (item: Omit<T, "id">): Promise<T> =>
      fetchData<T>(`/api/${type}/`, {
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

    search: <Q>(query: Q): Promise<T[]> =>
      fetchData<T[]>(`/api/${type}/search`, {
        method: "POST",
        body: JSON.stringify(query),
      }),
  };
}

// --- API Modules ---

export const eventAPI = {
  ...createCrudMethods<Event>("events"),

  getTodays: (): Promise<Event[]> => fetchData<Event[]>("/api/events/today"),
};

export const taskAPI = {
  ...createCrudMethods<Task>("tasks"),

  getTodays: (): Promise<Task[]> => fetchData<Task[]>("/api/tasks/today/"),

  setTaskStatus: (task: Task, status: string): Promise<Task> =>
    fetchData<Task>(`/api/tasks/${task.date}/${task.id}/actions`, {
      method: "POST",
      body: JSON.stringify({ type: status }),
    }),
};

export const authAPI = {
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
};

export const alarmAPI = {
  stopAll: (): Promise<void> =>
    fetchData<void>("/api/sheppard/stop-alarm", { method: "PUT" }),
};

export const dayAPI = {
  getToday: (): Promise<DayContext> =>
    fetchData<DayContext>("/api/days/today/context"),

  getTomorrow: (): Promise<DayContext> =>
    fetchData<DayContext>("/api/days/tomorrow/context"),

  getContext: (date: string): Promise<DayContext> =>
    fetchData<DayContext>(`/api/days/${date}/context`),

  scheduleToday: (): Promise<Day> =>
    fetchData<Day>("/api/days/today/schedule", { method: "PUT" }),

  getTemplates: (): Promise<DayTemplate[]> =>
    fetchData<DayTemplate[]>("/api/days/templates/"),
};

export const planningAPI = {
  scheduleToday: (): Promise<DayContext> =>
    fetchData<DayContext>("/api/planning/schedule/today", { method: "PUT" }),

  previewToday: (): Promise<DayContext> =>
    fetchData<DayContext>("/api/planning/preview/today"),

  previewTomorrow: (): Promise<DayContext> =>
    fetchData<DayContext>("/api/planning/preview/tomorrow"),
};

export const pushAPI = {
  getSubscriptions: (): Promise<PushSubscription[]> =>
    fetchData<PushSubscription[]>("/api/push/subscriptions/"),

  deleteSubscription: (id: string): Promise<void> =>
    fetchData<void>(`/api/push/subscriptions/${id}`, { method: "DELETE" }),
};

export const dayTemplateAPI = {
  ...createCrudMethods<DayTemplate>("day-templates"),
};

export const taskDefinitionAPI = {
  ...createCrudMethods<TaskDefinition>("task-definitions"),

  getAvailable: (): Promise<TaskDefinition[]> =>
    fetchData<TaskDefinition[]>("/api/task-definitions/available/"),

  bulkCreate: (taskDefinitions: TaskDefinition[]): Promise<TaskDefinition[]> =>
    fetchData<TaskDefinition[]>("/api/task-definitions/bulk/", {
      method: "POST",
      body: JSON.stringify(taskDefinitions),
    }),
};

export const routineAPI = {
  ...createCrudMethods<Routine>("routines"),
  addTask: (
    routineId: string,
    payload: {
      task_definition_id: string;
      name?: string | null;
      schedule?: TaskSchedule | null;
    }
  ): Promise<Routine> =>
    fetchData<Routine>(`/api/routines/${routineId}/tasks`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTask: (
    routineId: string,
    taskDefinitionId: string,
    payload: { name?: string | null; schedule?: TaskSchedule | null }
  ): Promise<Routine> =>
    fetchData<Routine>(`/api/routines/${routineId}/tasks/${taskDefinitionId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  removeTask: (routineId: string, taskDefinitionId: string): Promise<Routine> =>
    fetchData<Routine>(`/api/routines/${routineId}/tasks/${taskDefinitionId}`, {
      method: "DELETE",
    }),
};
