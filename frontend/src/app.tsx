import { Router, useNavigate, Route } from "@solidjs/router";
import { Title, Meta, MetaProvider } from "@solidjs/meta";
import { Component, Suspense } from "solid-js";
import "./index.css";

import { onMount, onCleanup } from "solid-js";
import { NotificationProvider } from "./providers/notifications";
import { SheppardProvider } from "./providers/sheppard";

import Home from "./pages/home";
import Login from "./pages/login";
import DayView from "./pages/day/view";
import NavPage from "./pages/navigation/links";
import CalendarPage from "./pages/navigation/calendar";

import "./utils/icons";

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
    <SheppardProvider>
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
        <Route path="/today" component={Home} />
        <Route path="/login" component={Login} />
        <Route path="/nav/calendar" component={CalendarPage} />
        <Route path="/nav" component={NavPage} />
        <Route path="/day/:date" component={DayView} />
      </Router>
    </SheppardProvider>
  );
}
