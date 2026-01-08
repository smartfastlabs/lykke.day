/// <reference lib="webworker" />
import { precacheAndRoute } from "workbox-precaching";

declare const self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<unknown>;
};

// Precache build assets injected by Vite PWA / Workbox.
precacheAndRoute(self.__WB_MANIFEST);

interface PushPayload {
  title: string;
  body?: string;
  actions?: Array<{
    action: string;
    title: string;
    icon?: string;
  }>;
  url?: string;
}

const CACHE_NAME = "app-cache-v1";

self.addEventListener("push", (event: PushEvent) => {
  const data = (event.data?.json() as PushPayload | undefined) ?? null;

  if (!data) {
    return;
  }

  const options: NotificationOptions & {
    vibrate?: number[];
    actions?: PushPayload["actions"];
  } = {
    body: data.body,
    icon: "/icons/icon-192x192.png",
    vibrate: [200, 100, 200],
    actions: data.actions,
    data: {
      url: data.url,
      dateOfArrival: Date.now(),
      primaryKey: 1,
    },
  };

  event.waitUntil(
    Promise.all([
      self.registration.showNotification(data.title, options),
      self.clients
        .matchAll({ type: "window", includeUncontrolled: true })
        .then((clientList) => {
          for (const client of clientList) {
            client.postMessage({ type: "message", data });
          }
        }),
    ])
  );
});

self.addEventListener("notificationclick", (event: NotificationEvent) => {
  event.notification.close();
  const url =
    (event.notification.data as { url?: string } | undefined)?.url ?? "/";

  if (!url) {
    return;
  }

  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && "focus" in client) {
            client.focus();
            client.postMessage({ type: "NAVIGATE", url });
            return;
          }
        }

        return self.clients.openWindow(url);
      })
  );
});

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event: ExtendableEvent) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event: FetchEvent) => {
  const { request } = event;

  if (request.method !== "GET") {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        if (!response.ok && response.type !== "basic") {
          return response;
        }

        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));

        return response;
      })
      .catch(() =>
        caches
          .match(request)
          .then((cached) => cached ?? new Response(null, { status: 504 }))
      )
  );
});

export {};
