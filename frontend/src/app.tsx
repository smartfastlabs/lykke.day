import { Router, Route } from "@solidjs/router";
import { Title, Meta, MetaProvider } from "@solidjs/meta";
import { Component, Suspense } from "solid-js";
import { FontAwesomeIcon } from "solid-fontawesome";
import "./index.css";

import { config, library } from "@fortawesome/fontawesome-svg-core";
import "@fortawesome/fontawesome-svg-core/styles.css";
import {
  faCoffee,
  faUser,
  faChartBar,
  faCogs,
  faBroom,
  faFaceSmileWink,
  faGear,
} from "@fortawesome/free-solid-svg-icons";

import Home from "./components/pages/home";
import DayStart from "./components/pages/day/start";

library.add(
  faGear,
  faFaceSmileWink,
  faBroom,
  faCogs,
  faCoffee,
  faUser,
  faChartBar
);

config.autoAddCss = false;

import { onMount } from "solid-js";
import { NotificationProvider } from "./providers/notifications";
import { TaskProvider } from "./providers/tasks";
import SettingsButton from "./components/shared/settingsButton";

export default function App() {
  onMount(() => {
    console.log(navigator);
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
    if (Notification.permission === "granted") {
      setTimeout(() => {
        const notification = new Notification("Welcome back!", {
          body: "Thanks for returning to Todd's Daily Planner.",
          icon: "/images/icons/jasper/192.png", // Your PWA icon
        });
      }, 200);
    }
  });

  const enablePush = () => {
    console.log("Enabling push notifications...");
    if (Notification.permission === "granted") {
      const notification = new Notification("Ooops ;)", {
        body: "You're already subscribed to push notifications.",
        icon: "/images/icons/jasper/192.png", // Your PWA icon
      });
      notification.onclick = (event) => {
        event.preventDefault(); // Prevent the browser from focusing the Notification's tab
        console.log("Notification clicked!");
        // You can open a new tab, navigate to a specific URL, or perform other actions here
        window.open("https://www.example.com", "_blank");
      };
    } else if ("serviceWorker" in navigator) {
      console.log("Service Worker is supported");
      navigator.serviceWorker.ready.then((registration) => {
        registration.pushManager
          .subscribe({
            userVisibleOnly: true,
            applicationServerKey:
              "BNWaFxSOKFUzGfVP5DOYhDSS8Nf2W9ifg4_3pNsfEzDih5CfspqP7-Ncr_9jAuwkd8jaHZPHdc0zIqHE-IPDoF8",
          })
          .then(async (subscription) => {
            console.log("Push subscription:", JSON.stringify(subscription));
            const response = await fetch("/api/push/subscribe", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(subscription),
            });
            console.log("Push subscription response:", response);
          })
          .catch((error) => {
            console.error("Push subscription error:", error);
          });
      });
    } else {
      console.error("Service Worker is not supported in this browser.");
    }
  };

  return (
    <>
      <Router
        root={(props) => (
          <NotificationProvider>
            <TaskProvider>
              <MetaProvider>
                <Title>Todd's Daily Planer</Title>
                <Suspense>{props.children}</Suspense>
              </MetaProvider>
            </TaskProvider>
          </NotificationProvider>
        )}
      >
        <Route path="/" component={Home} />
        <Route path="/day/start" component={DayStart} />
      </Router>
      <SettingsButton onClick={enablePush} />
    </>
  );
}
