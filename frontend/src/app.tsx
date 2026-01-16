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
import Apps from "@/pages/apps";
import YouTube from "@/pages/youtube";
import Podcasts from "@/pages/podcasts";
import Resources from "@/pages/resources";
import HomeLayout from "@/pages/me/today/layout";
import PreviewView from "@/pages/me/today/preview";
import TasksView from "@/pages/me/today/tasks";
import EventsView from "@/pages/me/today/events";
import GoalsView from "@/pages/me/today/goals";
import EventsPage from "@/pages/me/events";
import NavigationLayout from "@/pages/me/navigation/layout";
import NavPage from "@/pages/me/navigation/links";
import CalendarPage from "@/pages/me/navigation/calendar";
import CommandsPage from "@/pages/me/navigation/commands";
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
import TimeBlocksPage from "@/pages/me/settings/time-blocks/index";
import NewTimeBlockPage from "@/pages/me/settings/time-blocks/new";
import TimeBlockDetailPage from "@/pages/me/settings/time-blocks/detail";
import CalendarsPage from "@/pages/me/settings/calendars/index";
import CalendarDetailPage from "@/pages/me/settings/calendars/detail";
import RecurringEventsPage from "@/pages/me/settings/recurring-events/index";
import RecurringEventSeriesDetailPage from "@/pages/me/settings/recurring-events/detail";
import CalendarRecurringEventsPage from "@/pages/me/settings/calendars/recurring-events";
import PushSubscriptionsPage from "@/pages/me/settings/push-subscriptions/index";
import PushSubscriptionDetailPage from "@/pages/me/settings/push-subscriptions/detail";
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
      <div class="min-h-screen relative overflow-hidden">
        {/* Background gradients */}
        <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

        {/* Decorative blurs */}
        <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
        <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

        <div class="relative z-10">
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
            <Route path="/apps" component={Apps} />
            <Route path="/youtube" component={YouTube} />
            <Route path="/podcasts" component={Podcasts} />
            <Route path="/resources" component={Resources} />
            <Route path="/login" component={Login} />
            <Route path="/register" component={Register} />
            <Route path="/forgot-password" component={ForgotPassword} />
            <Route path="/reset-password" component={ResetPassword} />
            <Route path="/early-access" component={EarlyAccess} />
            <Route
              path="/home"
              component={() => <Navigate href="/me/today" />}
            />

              <Route path="/me" component={AuthGuard}>
                <Route path="/" component={HomeLayout}>
                  <Route path="/" component={PreviewView} />
                  <Route path="/tasks" component={TasksView} />
                  <Route path="/events" component={EventsView} />
                  <Route path="/goals" component={GoalsView} />
                </Route>
                <Route path="/events" component={EventsPage} />
                <Route path="/today" component={HomeLayout}>
                  <Route path="/" component={PreviewView} />
                  <Route path="/tasks" component={TasksView} />
                  <Route path="/events" component={EventsView} />
                  <Route path="/goals" component={GoalsView} />
                </Route>
              <Route path="/nav" component={NavigationLayout}>
                <Route path="/" component={NavPage} />
                <Route path="/calendar" component={CalendarPage} />
                <Route path="/commands" component={CommandsPage} />
              </Route>
              <Route path="/settings" component={SettingsLayout}>
                <Route path="/" component={SettingsIndexPage} />
                <Route path="/profile" component={ProfileSettingsPage} />
                <Route path="/day-templates" component={DayTemplatesPage} />
                <Route
                  path="/day-templates/new"
                  component={NewDayTemplatePage}
                />
                <Route
                  path="/day-templates/:id"
                  component={DayTemplateDetailPage}
                />
                <Route
                  path="/task-definitions"
                  component={TaskDefinitionsPage}
                />
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
                <Route path="/time-blocks" component={TimeBlocksPage} />
                <Route path="/time-blocks/new" component={NewTimeBlockPage} />
                <Route
                  path="/time-blocks/:id"
                  component={TimeBlockDetailPage}
                />
                <Route path="/calendars" component={CalendarsPage} />
                <Route
                  path="/calendars/:id/recurring-events"
                  component={CalendarRecurringEventsPage}
                />
                <Route path="/calendars/:id" component={CalendarDetailPage} />
                <Route
                  path="/recurring-events"
                  component={RecurringEventsPage}
                />
                <Route
                  path="/recurring-events/:id"
                  component={RecurringEventSeriesDetailPage}
                />
                <Route
                  path="/push-subscriptions"
                  component={PushSubscriptionsPage}
                />
                <Route
                  path="/push-subscriptions/:id"
                  component={PushSubscriptionDetailPage}
                />
              </Route>
            </Route>

            <Route path="*" component={NotFound} />
          </Router>
        </div>
      </div>
    </NotificationProvider>
  );
}
