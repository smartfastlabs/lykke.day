self.addEventListener("push", function (event) {
  console.log("Push event received:", event);
  try {
    data = event.data.json();
  } catch {
    data = {
      title: "Planned Day",
      body: event.data ? event.data.text() : "New notification",
    };
  }
  const options = {
    body: data.body,
    icon: "/icons/192.png", // Your PWA icon
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1,
      data: data,
    },
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  console.log("Notification clicked:", event.notification.data);

  // const notificationData = event?.target?.data || {};
  // console.log(notificationData);

  // event.waitUntil(clients.openWindow(data.url || "/"));
});

const CACHE_NAME = 'app-cache-v1';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  console.log("FETCH", event)

  // Only cache GET requests (non-modifying)
  if (request.method !== 'GET') {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Don't cache opaque responses or errors
        if (!response.ok && response.type !== 'basic') {
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