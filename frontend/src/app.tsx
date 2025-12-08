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
import Today from "./components/pages/day/today";
import Tomorrow from "./components/pages/day/tomorrow";
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
            <MetaProvider>
              <Title>Todd's Daily Planer</Title>
              <Suspense>{props.children}</Suspense>
            </MetaProvider>
          </NotificationProvider>
        )}
      >
        <Route path="/" component={Today} />
        <Route path="/today" component={Today} />
        <Route path="/pwa" component={Today} />
        <Route path="/kiosk" component={Today} />
        <Route path="/tomorrow" component={Tomorrow} />
        <Route path="/day/print" component={DayPrint} />
      </Router>
    </>
  );
}
