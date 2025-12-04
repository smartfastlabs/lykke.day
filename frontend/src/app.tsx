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
import DayPrint from "./components/pages/day/print";

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
  });

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
        <Route path="/day/print" component={DayPrint} />
      </Router>
    </>
  );
}
