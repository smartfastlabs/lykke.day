import { Router, useNavigate, Route } from "@solidjs/router";
import { Title, Meta, MetaProvider } from "@solidjs/meta";
import { Component, Suspense } from "solid-js";
import "./index.css";

import { onMount, onCleanup } from "solid-js";
import { NotificationProvider } from "./providers/notifications";

import PushSubscriptions from "./components/pages/pushNotifications";
import Home from "./components/pages/home";
import Login from "./components/pages/login";
import Today from "./components/pages/day/today";
import Tomorrow from "./components/pages/day/tomorrow";
import DayPrint from "./components/pages/day/print";
import NavPage from "./components/pages/navigation";

import "./utils/icons";
import { TaskProvider } from "./providers/tasks";

function NavigationHandler() {
  const navigate = useNavigate();

  onMount(() => {
    const handleSWMessage = (event) => {
      if (event.data?.type === "NAVIGATE" && event.data?.url) {
        navigate(event.data.url);
      }
    };

    navigator.serviceWorker?.addEventListener("message", handleSWMessage);

    onCleanup(() => {
      navigator.serviceWorker?.removeEventListener("message", handleSWMessage);
    });

    if (window.location.pathname !== "/login") {
      const sessionCookie = document.cookie
        .split("; ")
        .find((row) => row.startsWith("logged_in_at="));

      if (!sessionCookie) {
        navigate("/login");
        return;
      }
    }
  });

  return null;
}

export default function App() {
  onMount(() => {
    // Skip auth check on login page to avoid redirect loop

    // Register service worker
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.log("SW registered: ", registration);
        })
        .catch((registrationError) => {
          console.log("SW registration failed: ", registrationError);
        });
    }
  });

  return (
    <TaskProvider>
      <Router
        root={(props) => (
          <NotificationProvider>
            <NavigationHandler />
            <MetaProvider>
              <Title>Todd's Daily Planer</Title>
              <Suspense>{props.children}</Suspense>
            </MetaProvider>
          </NotificationProvider>
        )}
      >
        <Route path="/" component={Home} />
        <Route path="/login" component={Login} />
        <Route path="/navigation" component={NavPage} />
        <Route path="/push-subscriptions" component={PushSubscriptions} />
        <Route path="/today" component={Today} />
        <Route path="/pwa" component={Today} />
        <Route path="/kiosk" component={Today} />
        <Route path="/tomorrow" component={Tomorrow} />
        <Route path="/day/print" component={DayPrint} />
      </Router>
    </TaskProvider>
  );
}
