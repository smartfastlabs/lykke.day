import { Router, useNavigate, Route, useLocation } from "@solidjs/router";
import { Title, Meta, MetaProvider } from "@solidjs/meta";
import { Component, Suspense } from "solid-js";
import "./index.css";

import { onMount, onCleanup, createEffect } from "solid-js";
import { NotificationProvider } from "./providers/notifications";
import { SheppardProvider } from "./providers/sheppard";
import { authAPI } from "./utils/api";

import Home from "./pages/home";
import Login from "./pages/login";
import Register from "./pages/register";
import DayView from "./pages/day/preview";
import NavPage from "./pages/navigation/links";
import CalendarPage from "./pages/navigation/calendar";
import NotificationsPage from "./pages/notifications/index";
import NotificationsSubscribePage from "./pages/notifications/subscribe";

import "./utils/icons";

function NavigationHandler() {
  const navigate = useNavigate();
  const location = useLocation();

  onMount(() => {
    const handleSWMessage = (event) => {
      console.log("SW message received:", event);
      if (event.data?.type === "NAVIGATE" && event.data?.url) {
        navigate(event.data.url);
      }
    };

    navigator.serviceWorker?.addEventListener("message", handleSWMessage);

    onCleanup(() => {
      navigator.serviceWorker?.removeEventListener("message", handleSWMessage);
    });
  });

  // Check authentication on every route change
  createEffect(() => {
    const pathname = location.pathname;
    // Allow access to login and register pages without authentication
    if (pathname === "/login" || pathname === "/register") {
      return;
    }

    // Check authentication asynchronously
    authAPI
      .me()
      .then((resp) => {
        // If the response is not ok (401 or other error), redirect to login
        if (!resp.ok || resp.status === 401) {
          navigate("/login");
        }
      })
      .catch(() => {
        // On any error, redirect to login
        navigate("/login");
      });
  });

  return null;
}

export default function App() {
  onMount(() => {
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
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/nav/calendar" component={CalendarPage} />
        <Route path="/nav" component={NavPage} />
        <Route path="/day/:date" component={DayView} />
        <Route path="/notifications" component={NotificationsPage} />
        <Route
          path="/notifications/subscribe"
          component={NotificationsSubscribePage}
        />
      </Router>
    </SheppardProvider>
  );
}
