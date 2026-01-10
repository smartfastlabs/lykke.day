import { Title, MetaProvider } from "@solidjs/meta";
import { Navigate, Route, Router, useNavigate } from "@solidjs/router";
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
import FAQ from "@/pages/faq";
import Books from "@/pages/books";
import TodoApps from "@/pages/todo-apps";
import MeditationApps from "@/pages/meditation-apps";
import WeightLossApps from "@/pages/weight-loss-apps";
import HabitApps from "@/pages/habit-apps";
import HappinessApps from "@/pages/happiness-apps";
import YouTube from "@/pages/youtube";
import Podcasts from "@/pages/podcasts";
import Resources from "@/pages/resources";
import ThereIsAnAppForThat from "@/pages/there-is-an-app-for-that";
import HomeLayout from "@/pages/me/home/layout";
import PreviewView from "@/pages/me/home/preview";
import DoItView from "@/pages/me/home/doit";
import TasksView from "@/pages/me/home/tasks";
import EventsView from "@/pages/me/home/events";
import SheppardView from "@/pages/me/home/sheppard";
import DayView from "@/pages/me/day/preview";
import NavPage from "@/pages/me/navigation/links";
import CalendarPage from "@/pages/me/navigation/calendar";
import NotificationsPage from "@/pages/me/notifications/index";
import NotificationsSubscribePage from "@/pages/me/notifications/subscribe";
import SettingsLayout from "@/pages/me/settings/layout";
import SettingsIndexPage from "@/pages/me/settings/index";
import ProfileSettingsPage from "@/pages/me/settings/profile";
import DayTemplatesPage from "@/pages/me/settings/day-templates/index";
import NewDayTemplatePage from "@/pages/me/settings/day-templates/new";
import DayTemplateDetailPage from "@/pages/me/settings/day-templates/detail";
import TaskDefinitionsPage from "@/pages/me/settings/task-definitions/index";
import NewTaskDefinitionPage from "@/pages/me/settings/task-definitions/new";
import TaskDefinitionDetailPage from "@/pages/me/settings/task-definitions/detail";
import RoutinesPage from "@/pages/me/settings/routines/index";
import NewRoutinePage from "@/pages/me/settings/routines/new";
import RoutineDetailPage from "@/pages/me/settings/routines/detail";
import CalendarsPage from "@/pages/me/settings/calendars/index";
import CalendarDetailPage from "@/pages/me/settings/calendars/detail";
import RecurringEventsPage from "@/pages/me/settings/recurring-events/index";
import RecurringEventSeriesDetailPage from "@/pages/me/settings/recurring-events/detail";
import CalendarRecurringEventsPage from "@/pages/me/settings/calendars/recurring-events";
import Welcome from "@/pages/me/welcome";
import OverviewPage from "@/pages/me/overview";
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
        .register("/sw.js", { type: "classic" })
        .then((registration) => {
          console.log("PWA service worker registered:", registration);
        })
        .catch((error) => {
          console.error("PWA service worker registration failed:", error);
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
        <Route path="/faq" component={FAQ} />
        <Route path="/books" component={Books} />
        <Route path="/apps" component={ThereIsAnAppForThat} />
        <Route path="/apps/todo" component={TodoApps} />
        <Route path="/apps/meditation" component={MeditationApps} />
        <Route path="/apps/weight-loss" component={WeightLossApps} />
        <Route path="/apps/habits" component={HabitApps} />
        <Route path="/apps/happiness" component={HappinessApps} />
        <Route path="/youtube" component={YouTube} />
        <Route path="/podcasts" component={Podcasts} />
        <Route path="/resources" component={Resources} />
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
          <Route path="/" component={() => <Navigate href="/me/today" />} />
          <Route path="/today" component={HomeLayout}>
            <Route path="/" component={PreviewView} />
            <Route path="/doit" component={DoItView} />
            <Route path="/tasks" component={TasksView} />
            <Route path="/events" component={EventsView} />
            <Route path="/sheppard" component={SheppardView} />
          </Route>
          <Route path="/overview" component={OverviewPage} />
          <Route path="/welcome" component={Welcome} />
          <Route path="/day/:date" component={DayView} />
          <Route path="/nav/calendar" component={CalendarPage} />
          <Route path="/nav" component={NavPage} />
          <Route path="/notifications" component={NotificationsPage} />
          <Route
            path="/notifications/subscribe"
            component={NotificationsSubscribePage}
          />
          <Route path="/settings" component={SettingsLayout}>
            <Route path="/" component={SettingsIndexPage} />
            <Route path="/profile" component={ProfileSettingsPage} />
            <Route path="/day-templates" component={DayTemplatesPage} />
            <Route path="/day-templates/new" component={NewDayTemplatePage} />
            <Route
              path="/day-templates/:id"
              component={DayTemplateDetailPage}
            />
            <Route path="/task-definitions" component={TaskDefinitionsPage} />
            <Route
              path="/task-definitions/new"
              component={NewTaskDefinitionPage}
            />
            <Route
              path="/task-definitions/:id"
              component={TaskDefinitionDetailPage}
            />
            <Route path="/routines" component={RoutinesPage} />
            <Route path="/routines/new" component={NewRoutinePage} />
            <Route path="/routines/:id" component={RoutineDetailPage} />
            <Route path="/calendars" component={CalendarsPage} />
            <Route
              path="/calendars/:id/recurring-events"
              component={CalendarRecurringEventsPage}
            />
            <Route path="/calendars/:id" component={CalendarDetailPage} />
            <Route path="/recurring-events" component={RecurringEventsPage} />
            <Route
              path="/recurring-events/:id"
              component={RecurringEventSeriesDetailPage}
            />
          </Route>
        </Route>

        <Route path="*" component={NotFound} />
      </Router>
    </NotificationProvider>
  );
}
