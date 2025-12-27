self.addEventListener("push", function (event) {
  console.log("Push event received:", event);
  data = event.data.json();
  const options = {
    body: data.body,
    icon: "/icons/192.png", // Your PWA icon
    vibrate: [200, 100, 200],
    actions: data.actions,
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1,
    },
  };
  console.log("Showing notification:", data.title, options);

  event.waitUntil(self.registration.showNotification(data.title, options));
  self.clients
    .matchAll({ type: "window", includeUncontrolled: true })
    .then((clientList) => {
      for (const client of clientList) {
        client.postMessage({ type: "message", data });
      }
    });
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  const url = event.notification.data?.url || "/";

  if (url) {
    event.waitUntil(
      clients
        .matchAll({ type: "window", includeUncontrolled: true })
        .then((clientList) => {
          // If app is already open, focus it and send message
          for (const client of clientList) {
            if (
              client.url.includes(self.location.origin) &&
              "focus" in client
            ) {
              client.focus();
              client.postMessage({ type: "NAVIGATE", url });
              return;
            }
          }
          // No window open, open a new one directly to the URL
          return clients.openWindow(url);
        })
    );
  }
});

const CACHE_NAME = "app-cache-v1";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Only cache GET requests (non-modifying)
  if (request.method !== "GET") {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Don't cache opaque responses or errors
        if (!response.ok && response.type !== "basic") {
          return response;
        }

        // Cache the successful response
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));

        return response;
      })
      .catch(() => caches.match(request))
  );
});
