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

const isDev = process.env.NODE_ENV === "development";

function getHeaders(headers) {
  const event = getRequestEvent();
  const cookieHeader = event?.request.headers.get("cookie");
  headers = headers || {
    "Content-Type": "application/json",
  };

  if (cookieHeader && !headers["Cookie"]) {
    // If the headers object doesn't already have a Cookie header, add it
    headers["Cookie"] = cookieHeader;
  }

  return headers;
}

async function fetchJSON(
  url: string,
  options: object = { suppressError: false }
): any {
  options.headers = getHeaders(options.headers);

  console.log("Fetching URL:", url, "with options:", options);
  const response = await fetch(url, options);
  const body = await response.json();

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
    globalNotifications.add(`Error fetching data: ${body.detail}`, "error");
  }

  return {
    data: body,
    status: response.status,
    ok: response.ok,
  };
}

function putMethod(type: string) {
  return async function (item: any) {
    const url = item.id ? `/api/${type}/${item.id}` : `/api/${type}`;
    return fetchJSON(url, {
      method: "PUT",
      body: JSON.stringify(item),
      headers: {
        "Content-Type": "application/json",
      },
    });
  };
}

function postMethod(type: string) {
  return async function (item: any) {
    const url = item.id ? `/api/${type}/${item.id}` : `/api/${type}`;
    return fetchJSON(url, {
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

export function readOnly(type: string) {
  return {
    get: (u: string) => fetchJSON(`/api/${type}/${u}`),
    search: postMethod(`${type}/search`),
  };
}

export function genericCrud(type) {
  return {
    get: (u: string) => fetchJSON(`/api/${type}/${u}`),
    search: postMethod(`${type}/search`),
    delete: deleteMethod(type),
    update: putMethod(type),
    create: postMethod(type),
  };
}

export const eventAPI = {
  ...genericCrud("events"),

  getTodays: async (): Event[] => {
    const resp = await fetchJSON(`/api/events/today`, {
      method: "GET",
    });

    return resp.data as Event[];
  },
};

export const taskAPI = {
  ...genericCrud("tasks"),

  getTodays: async (): Event[] => {
    const resp = await fetchJSON(`/api/tasks/today`, {
      method: "GET",
    });

    return resp.data as Event[];
  },

  setTaskStatus: async (task: Task, status: string): Task => {
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
  login: async (email: string, password: string): any => {
    const resp = await fetchJSON("/api/auth/login", {
      method: "PUT",
      body: JSON.stringify({ email, password }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    return resp.data;
  },
  register: async (
    email: string,
    password: string,
    phoneNumber?: string | null
  ): any => {
    const resp = await fetchJSON("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        confirm_password: password,
        phone_number: phoneNumber || null,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    return resp.data;
  },
};

export const alarmAPI = {
  stopAll: async (): null => {
    fetchJSON("/api/sheppard/stop-alarm", {
      method: "PUT",
    });
  },
};

export const dayAPI = {
  scheduleToday: async (): Day => {
    const resp = await fetchJSON("/api/days/today/schedule", {
      method: "PUT",
    });

    return resp.data as Day;
  },
  getTomorrow: async (): DayContext => {
    const resp = await fetchJSON("/api/days/tomorrow/context", {
      method: "GET",
    });

    return resp.data as DayContext;
  },
  getTemplates: async (): DayTemplate[] => {
    const resp = await fetchJSON("/api/days/templates", {
      method: "GET",
    });

    return resp.data as DayTemplate[];
  },

  getToday: async (): DayContext => {
    const resp = await fetchJSON("/api/days/today/context", {
      method: "GET",
    });

    return resp.data as DayContext;
  },

  getContext: async (date: string): DayContext => {
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
    const resp = await fetchJSON("/api/day-templates/", {
      method: "GET",
    });

    // Handle paginated response - extract items array
    if (resp.data && resp.data.items) {
      return resp.data.items as DayTemplate[];
    }
    // Fallback to direct array if not paginated
    return resp.data as DayTemplate[];
  },
};

export const taskDefinitionAPI = {
  ...genericCrud("task-definitions"),

  getAll: async (): Promise<TaskDefinition[]> => {
    const resp = await fetchJSON("/api/task-definitions/", {
      method: "GET",
    });

    // Handle paginated response - extract items array
    if (resp.data && resp.data.items) {
      return resp.data.items as TaskDefinition[];
    }
    // Fallback to direct array if not paginated
    return resp.data as TaskDefinition[];
  },
};
