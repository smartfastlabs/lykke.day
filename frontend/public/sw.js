self.addEventListener("push", function (event) {
  console.log("Push event received:", event);
  try {
    data = event.data.json();
  } catch {
    data = {
      title: "Jasper Grief",
      body: event.data ? event.data.text() : "New notification",
    };
  }
  const options = {
    body: data.body,
    icon: "/images/icons/jasper/192.png", // Your PWA icon
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
  console.log("Notification clicked:", event.target.data);

  const notificationData = event?.target?.data || {};
  console.log(notificationData);

  // event.waitUntil(clients.openWindow(data.url || "/"));
});
