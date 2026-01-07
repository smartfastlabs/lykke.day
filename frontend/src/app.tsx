import { Navigate, Route, Router, useNavigate } from "@solidjs/router";
import { Title, MetaProvider } from "@solidjs/meta";
import { Suspense, onMount, onCleanup } from "solid-js";
import "@/index.css";

import { NotificationProvider } from "@/providers/notifications";
import { AuthProvider } from "@/providers/auth";
import { AuthGuard } from "@/providers/authGuard";

import Login from "@/pages/login";
import Register from "@/pages/register";
import ForgotPassword from "@/pages/forgot-password";
import ResetPassword from "@/pages/reset-password";
import EarlyAccess from "@/pages/early-access";
import Landing from "@/pages/landing";
import Privacy from "@/pages/privacy";
import Terms from "@/pages/terms";
import Home from "@/pages/me";
import DayView from "@/pages/me/day/preview";
import NavPage from "@/pages/me/navigation/links";
import CalendarPage from "@/pages/me/navigation/calendar";
import NotificationsPage from "@/pages/me/notifications/index";
import NotificationsSubscribePage from "@/pages/me/notifications/subscribe";
import SettingsPage from "@/pages/me/settings/index";
import DayTemplatesPage from "@/pages/me/settings/day-templates/index";
import NewDayTemplatePage from "@/pages/me/settings/day-templates/new";
import DayTemplateDetailPage from "@/pages/me/settings/day-templates/detail";
import TaskDefinitionsPage from "@/pages/me/settings/task-definitions/index";
import NewTaskDefinitionPage from "@/pages/me/settings/task-definitions/new";
import TaskDefinitionDetailPage from "@/pages/me/settings/task-definitions/detail";
import RoutinesPage from "@/pages/me/settings/routines/index";
import NewRoutinePage from "@/pages/me/settings/routines/new";
import RoutineDetailPage from "@/pages/me/settings/routines/detail";
import Welcome from "@/pages/me/welcome";
import NotFound from "@/pages/not-found";

import "@/utils/icons";

function NavigationHandler() {
  const navigate = useNavigate();

  onMount(() => {
    const handleSWMessage = (event: MessageEvent): void => {
      console.log("SW message received:", event);
      if (event.data?.type === "NAVIGATE" && event.data?.url) {
        navigate(event.data.url as string);
      }
    };

    navigator.serviceWorker?.addEventListener("message", handleSWMessage);

    onCleanup(() => {
      navigator.serviceWorker?.removeEventListener("message", handleSWMessage);
    });
  });

  return null;
}

export default function App() {
  onMount(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration: ServiceWorkerRegistration) => {
          console.log("SW registered: ", registration);
        })
        .catch((registrationError: unknown) => {
          console.log("SW registration failed: ", registrationError);
        });
    }
  });

  return (
    <NotificationProvider>
      <Router
        root={(props) => (
          <AuthProvider>
            <NavigationHandler />
            <MetaProvider>
              <Title>Todd's Daily Planer</Title>
              <Suspense>{props.children}</Suspense>
            </MetaProvider>
          </AuthProvider>
        )}
      >
        <Route path="/" component={Landing} />
        <Route path="/privacy" component={Privacy} />
        <Route path="/terms" component={Terms} />
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/forgot-password" component={ForgotPassword} />
        <Route path="/reset-password" component={ResetPassword} />
        <Route path="/early-access" component={EarlyAccess} />
        <Route
          path="/welcome"
          component={() => <Navigate href="/me/welcome" />}
        />
        <Route path="/home" component={() => <Navigate href="/me" />} />

        <Route path="/me" component={AuthGuard}>
          <Route path="/" component={Home} />
          <Route path="/welcome" component={Welcome} />
          <Route path="/day/:date" component={DayView} />
          <Route path="/nav/calendar" component={CalendarPage} />
          <Route path="/nav" component={NavPage} />
          <Route path="/notifications" component={NotificationsPage} />
          <Route
            path="/notifications/subscribe"
            component={NotificationsSubscribePage}
          />
          <Route path="/settings" component={SettingsPage} />
          <Route path="/settings/day-templates" component={DayTemplatesPage} />
          <Route
            path="/settings/day-templates/new"
            component={NewDayTemplatePage}
          />
          <Route
            path="/settings/day-templates/:id"
            component={DayTemplateDetailPage}
          />
          <Route
            path="/settings/task-definitions"
            component={TaskDefinitionsPage}
          />
          <Route
            path="/settings/task-definitions/new"
            component={NewTaskDefinitionPage}
          />
          <Route
            path="/settings/task-definitions/:id"
            component={TaskDefinitionDetailPage}
          />
          <Route path="/settings/routines" component={RoutinesPage} />
          <Route path="/settings/routines/new" component={NewRoutinePage} />
          <Route path="/settings/routines/:id" component={RoutineDetailPage} />
        </Route>

        <Route path="*" component={NotFound} />
      </Router>
    </NotificationProvider>
  );
}
