import { getRequestEvent } from "solid-js/web";

import { globalNotifications } from "../providers/notifications";
import {
  Event,
  Task,
  Day,
  DayContext,
  DayTemplate,
  TaskDefinition,
  PushSubscription,
} from "../types/api";
import type { ApiResponse, ApiError } from "../types/api/utils";

const isDev = process.env.NODE_ENV === "development";

interface FetchOptions extends RequestInit {
  suppressError?: boolean;
  headers?: HeadersInit;
}

function getHeaders(headers?: HeadersInit): HeadersInit {
  const event = getRequestEvent();
  const cookieHeader = event?.request.headers.get("cookie");
  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const mergedHeaders = headers ? { ...defaultHeaders, ...headers } : defaultHeaders;

  if (cookieHeader && !(mergedHeaders as Record<string, string>)["Cookie"]) {
    // If the headers object doesn't already have a Cookie header, add it
    (mergedHeaders as Record<string, string>)["Cookie"] = cookieHeader;
  }

  return mergedHeaders;
}

async function fetchJSON<T = unknown>(
  url: string,
  options: FetchOptions = { suppressError: false }
): Promise<ApiResponse<T>> {
  const headers = getHeaders(options.headers);

  console.log("Fetching URL:", url, "with options:", options);
  const response = await fetch(url, { ...options, headers });
  const body = (await response.json()) as T | ApiError;

  // Handle 401 Unauthorized - redirect to login
  if (response.status === 401) {
    globalNotifications.add("Not Logged In", "error");
    // Only redirect if not already on login page to avoid infinite redirects
    if (["/login", "/register"].includes(window.location.pathname)) {
      console.log(
        "Already on login or register page, not redirecting",
        window.location.pathname
      );
      return Promise.reject(new Error("Unauthorized"));
    }
    window.location.href = "/login";
  }

  if (!response.ok && !options.suppressError) {
    const errorBody = body as ApiError;
    globalNotifications.add(
      `Error fetching data: ${errorBody.detail || "Unknown error"}`,
      "error"
    );
  }

  return {
    data: body as T,
    status: response.status,
    ok: response.ok,
  };
}

interface EntityWithId {
  id?: string;
}

function putMethod<T extends EntityWithId>(type: string) {
  return async function (item: T): Promise<ApiResponse<T>> {
    const url = item.id ? `/api/${type}/${item.id}` : `/api/${type}`;
    return fetchJSON<T>(url, {
      method: "PUT",
      body: JSON.stringify(item),
      headers: {
        "Content-Type": "application/json",
      },
    });
  };
}

function postMethod<T extends EntityWithId>(type: string) {
  return async function (item: T): Promise<ApiResponse<T>> {
    const url = item.id ? `/api/${type}/${item.id}` : `/api/${type}`;
    return fetchJSON<T>(url, {
      method: "POST",
      body: JSON.stringify(item),
      headers: {
        "Content-Type": "application/json",
      },
    });
  };
}

function deleteMethod(type: string) {
  return async function (id: string) {
    return fetchJSON(`/api/${type}/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });
  };
}

export function readOnly<T extends EntityWithId>(type: string) {
  return {
    get: (u: string): Promise<ApiResponse<T>> => fetchJSON<T>(`/api/${type}/${u}`),
    search: postMethod<T>(`${type}/search`),
  };
}

export function genericCrud<T extends EntityWithId>(type: string) {
  return {
    get: (u: string): Promise<ApiResponse<T>> => fetchJSON<T>(`/api/${type}/${u}`),
    search: postMethod<T>(`${type}/search`),
    delete: deleteMethod(type),
    update: putMethod<T>(type),
    create: postMethod<T>(type),
  };
}

export const eventAPI = {
  ...genericCrud("events"),

  getTodays: async (): Promise<Event[]> => {
    const resp = await fetchJSON(`/api/events/today`, {
      method: "GET",
    });

    return resp.data as Event[];
  },
};

export const taskAPI = {
  ...genericCrud("tasks"),

  getTodays: async (): Promise<Task[]> => {
    const resp = await fetchJSON<Task[]>(`/api/tasks/today`, {
      method: "GET",
    });

    return resp.data;
  },

  setTaskStatus: async (task: Task, status: string): Promise<Task> => {
    const resp = await fetchJSON(`/api/tasks/${task.date}/${task.id}/actions`, {
      method: "POST",
      body: JSON.stringify({
        type: status,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    return resp.data as Task;
  },
};
export const authAPI = {
  login: async (email: string, password: string): Promise<void> => {
    // FastAPI Users uses form-urlencoded for login with OAuth2 spec
    // where "username" is the email field
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch("/api/auth/login", {
      method: "POST",
      body: formData,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Login failed");
    }
    // 204 No Content on success - cookie is set automatically
  },

  register: async (email: string, password: string): Promise<unknown> => {
    const resp = await fetchJSON("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!resp.ok) {
      const errorData = resp.data as ApiError;
      throw new Error(errorData.detail || "Registration failed");
    }

    return resp.data;
  },

  logout: async (): Promise<void> => {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Logout failed");
    }
  },
};

export const alarmAPI = {
  stopAll: async (): Promise<void> => {
    await fetchJSON("/api/sheppard/stop-alarm", {
      method: "PUT",
    });
  },
};

export const dayAPI = {
  scheduleToday: async (): Promise<Day> => {
    const resp = await fetchJSON("/api/days/today/schedule", {
      method: "PUT",
    });

    return resp.data as Day;
  },
  getTomorrow: async (): Promise<DayContext> => {
    const resp = await fetchJSON("/api/days/tomorrow/context", {
      method: "GET",
    });

    return resp.data as DayContext;
  },
  getTemplates: async (): Promise<DayTemplate[]> => {
    const resp = await fetchJSON("/api/days/templates", {
      method: "GET",
    });

    return resp.data as DayTemplate[];
  },

  getToday: async (): Promise<DayContext> => {
    const resp = await fetchJSON("/api/days/today/context", {
      method: "GET",
    });

    return resp.data as DayContext;
  },

  getContext: async (date: string): Promise<DayContext> => {
    const resp = await fetchJSON(`/api/days/${date}/context`, {
      method: "GET",
    });

    return resp.data as DayContext;
  },
};

export const planningAPI = {
  scheduleToday: async (): Promise<DayContext> => {
    const resp = await fetchJSON("/api/planning/schedule/today", {
      method: "PUT",
    });

    return resp.data as DayContext;
  },
  previewToday: async (): Promise<DayContext> => {
    const resp = await fetchJSON("/api/planning/preview/today", {
      method: "GET",
    });

    return resp.data as DayContext;
  },
  previewTomorrow: async (): Promise<DayContext> => {
    const resp = await fetchJSON("/api/planning/preview/tomorrow", {
      method: "GET",
    });

    return resp.data as DayContext;
  },
};

export const pushAPI = {
  getSubscriptions: async (): Promise<PushSubscription[]> => {
    const resp = await fetchJSON("/api/push/subscriptions", {
      method: "GET",
    });

    return resp.data as PushSubscription[];
  },
  deleteSubscription: async (id: string): Promise<void> => {
    await fetchJSON(`/api/push/subscriptions/${id}`, {
      method: "DELETE",
    });
  },
};

export const dayTemplateAPI = {
  ...genericCrud("day-templates"),

  getAll: async (): Promise<DayTemplate[]> => {
    const resp = await fetchJSON<DayTemplate[] | { items: DayTemplate[] }>("/api/day-templates/", {
      method: "GET",
    });

    // Handle paginated response - extract items array
    if (resp.data && typeof resp.data === 'object' && 'items' in resp.data) {
      return (resp.data as { items: DayTemplate[] }).items;
    }
    // Fallback to direct array if not paginated
    return resp.data as DayTemplate[];
  },
};

export const taskDefinitionAPI = {
  ...genericCrud("task-definitions"),

  getAll: async (): Promise<TaskDefinition[]> => {
    const resp = await fetchJSON<TaskDefinition[] | { items: TaskDefinition[] }>("/api/task-definitions/", {
      method: "GET",
    });

    // Handle paginated response - extract items array
    if (resp.data && typeof resp.data === 'object' && 'items' in resp.data) {
      return (resp.data as { items: TaskDefinition[] }).items;
    }
    // Fallback to direct array if not paginated
    return resp.data as TaskDefinition[];
  },

  getAvailable: async (): Promise<TaskDefinition[]> => {
    const resp = await fetchJSON("/api/task-definitions/available", {
      method: "GET",
    });

    return resp.data as TaskDefinition[];
  },

  bulkCreate: async (
    taskDefinitions: TaskDefinition[]
  ): Promise<TaskDefinition[]> => {
    const resp = await fetchJSON("/api/task-definitions/bulk", {
      method: "POST",
      body: JSON.stringify(taskDefinitions),
      headers: {
        "Content-Type": "application/json",
      },
    });

    return resp.data as TaskDefinition[];
  },
};
