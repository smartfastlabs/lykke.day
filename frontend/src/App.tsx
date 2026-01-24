import { Title, MetaProvider } from "@solidjs/meta";
import { Navigate, Route, Router, useNavigate } from "@solidjs/router";
import { Suspense, onMount, onCleanup } from "solid-js";
import "@/index.css";

import { NotificationProvider } from "@/providers/notifications";
import { AuthProvider } from "@/providers/auth";
import { AuthGuard } from "@/providers/authGuard";
import CookieDisclaimer from "@/components/shared/CookieDisclaimer";

import Login from "@/pages/Login";
import Register from "@/pages/Register";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import EarlyAccess from "@/pages/EarlyAccess";
import Landing from "@/pages/Landing";
import Privacy from "@/pages/Privacy";
import Terms from "@/pages/Terms";
import FAQ from "@/pages/FAQ";
import Books from "@/pages/Books";
import Apps from "@/pages/Apps";
import YouTube from "@/pages/YouTube";
import Podcasts from "@/pages/Podcasts";
import Resources from "@/pages/Resources";
import Install from "@/pages/Install";
import HomeLayout from "@/pages/me/today/Layout";
import PreviewView from "@/pages/me/today/Preview";
import TasksView from "@/pages/me/today/Tasks";
import EventsView from "@/pages/me/today/Events";
import RemindersView from "@/pages/me/today/Reminders";
import TodayEditPage from "@/pages/me/today/Edit";
import ThatsAllPage from "@/pages/me/today/ThatsAll";
import AddAdhocTaskPage from "@/pages/me/today/AddAdhocTask";
import AddReminderPage from "@/pages/me/today/AddReminder";
import BrainDumpPage from "@/pages/me/BrainDump";
import BrainDumpDumpPage from "@/pages/me/BrainDumpDump";
import NavigationLayout from "@/pages/me/navigation/Layout";
import NavPage from "@/pages/me/navigation/Links";
import CalendarPage from "@/pages/me/navigation/Calendar";
import CommandsPage from "@/pages/me/navigation/Commands";
import SettingsLayout from "@/pages/me/settings/Layout";
import SettingsIndexPage from "@/pages/me/settings/Index";
import ProfileSettingsPage from "@/pages/me/settings/Profile";
import LLMSettingsPage from "@/pages/me/settings/llm/Index";
import DayTemplatesPage from "@/pages/me/settings/day-templates/Index";
import NewDayTemplatePage from "@/pages/me/settings/day-templates/New";
import DayTemplateDetailPage from "@/pages/me/settings/day-templates/Detail";
import NotificationConfigPage from "@/pages/me/settings/notifications/Index";
import TaskDefinitionsPage from "@/pages/me/settings/task-definitions/Index";
import NewTaskDefinitionPage from "@/pages/me/settings/task-definitions/New";
import TaskDefinitionDetailPage from "@/pages/me/settings/task-definitions/Detail";
import RoutineDefinitionsPage from "@/pages/me/settings/routine-definitions/Index";
import NewRoutineDefinitionPage from "@/pages/me/settings/routine-definitions/New";
import RoutineDefinitionDetailPage from "@/pages/me/settings/routine-definitions/Detail";
import TimeBlocksPage from "@/pages/me/settings/time-blocks/Index";
import NewTimeBlockPage from "@/pages/me/settings/time-blocks/New";
import TimeBlockDetailPage from "@/pages/me/settings/time-blocks/Detail";
import CalendarsPage from "@/pages/me/settings/calendars/Index";
import CalendarDetailPage from "@/pages/me/settings/calendars/Detail";
import RecurringEventsPage from "@/pages/me/settings/recurring-events/Index";
import RecurringEventSeriesDetailPage from "@/pages/me/settings/recurring-events/Detail";
import CalendarRecurringEventsPage from "@/pages/me/settings/calendars/RecurringEvents";
import PushSubscriptionsPage from "@/pages/me/settings/push-subscriptions/Index";
import PushSubscriptionDetailPage from "@/pages/me/settings/push-subscriptions/Detail";
import NotFound from "@/pages/NotFound";

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
      let registration: ServiceWorkerRegistration | null = null;
      let isReloading = false;
      let hasUpdate = false;

      // Handle controller change - reload when new SW takes control
      const handleControllerChange = (): void => {
        if (!hasUpdate || isReloading) return;
        isReloading = true;
        window.location.reload();
      };

      // Check for updates
      const checkForUpdates = (): void => {
        if (registration) {
          registration.update().catch((error) => {
            console.error("Service worker update check failed:", error);
          });
        }
      };

      // Register service worker
      navigator.serviceWorker
        .register("/sw.js", { type: "classic" })
        .then((reg) => {
          registration = reg;
          console.log("PWA service worker registered:", reg);

          // Listen for controller change (new SW activated)
          navigator.serviceWorker.addEventListener(
            "controllerchange",
            handleControllerChange
          );

          // Listen for update found
          reg.addEventListener("updatefound", () => {
            const newWorker = reg.installing;
            if (newWorker) {
              newWorker.addEventListener("statechange", () => {
                // When new worker is installed and waiting, it will activate
                // due to skipWaiting() in sw.ts, triggering controllerchange
                if (
                  newWorker.state === "installed" &&
                  navigator.serviceWorker.controller
                ) {
                  hasUpdate = true;
                  // New version is ready, controllerchange will fire soon
                  console.log("New service worker version installed");
                }
              });
            }
          });

          // Check for updates on page visibility change (user returns to tab)
          const handleVisibilityChange = (): void => {
            if (!document.hidden) {
              checkForUpdates();
            }
          };

          document.addEventListener("visibilitychange", handleVisibilityChange);

          // Check for updates periodically (every hour)
          const updateInterval = setInterval(checkForUpdates, 60 * 60 * 1000);

          // Initial update check
          checkForUpdates();

          // Cleanup
          onCleanup(() => {
            navigator.serviceWorker.removeEventListener(
              "controllerchange",
              handleControllerChange
            );
            document.removeEventListener(
              "visibilitychange",
              handleVisibilityChange
            );
            clearInterval(updateInterval);
          });
        })
        .catch((error) => {
          console.error("PWA service worker registration failed:", error);
        });
    }
  });

  return (
    <NotificationProvider>
      <div class="min-h-screen relative overflow-hidden" style={{ "min-height": "100dvh" }}>
        {/* Background gradients - use fixed positioning to cover entire viewport including notch */}
        <div class="fixed inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" style={{ "top": "0", "left": "0", "right": "0", "bottom": "0" }} />
        <div class="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" style={{ "top": "0", "left": "0", "right": "0", "bottom": "0" }} />
        <div class="fixed inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" style={{ "top": "0", "left": "0", "right": "0", "bottom": "0" }} />

        {/* Decorative blurs - also fixed */}
        <div class="fixed top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
        <div class="fixed bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

        {/* Content with safe area padding */}
        <div 
          class="relative z-10" 
          style={{
            "padding-top": "env(safe-area-inset-top)",
            "padding-left": "env(safe-area-inset-left)",
            "padding-right": "env(safe-area-inset-right)",
            "padding-bottom": "env(safe-area-inset-bottom)"
          }}
        >
          <Router
            root={(props) => (
              <AuthProvider>
                <NavigationHandler />
                <MetaProvider>
                  <Title>lykke.day</Title>
                  <Suspense>{props.children}</Suspense>
                  <CookieDisclaimer />
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
            <Route path="/install" component={Install} />
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
                <Route path="/edit" component={TodayEditPage} />
              </Route>
              <Route path="/brain-dump" component={BrainDumpPage} />
              <Route path="/brain-dump/dump" component={BrainDumpDumpPage} />
              <Route path="/adhoc-task" component={AddAdhocTaskPage} />
              <Route path="/add-reminder" component={AddReminderPage} />
              <Route path="/thats-all-for-today" component={ThatsAllPage} />
              <Route path="/today" component={HomeLayout}>
                <Route path="/" component={PreviewView} />
                <Route path="/tasks" component={TasksView} />
                <Route path="/events" component={EventsView} />
                <Route path="/reminders" component={RemindersView} />
                <Route path="/edit" component={TodayEditPage} />
              </Route>
              <Route path="/nav" component={NavigationLayout}>
                <Route path="/" component={NavPage} />
                <Route path="/calendar" component={CalendarPage} />
                <Route path="/commands" component={CommandsPage} />
              </Route>
              <Route path="/settings" component={SettingsLayout}>
                <Route path="/" component={SettingsIndexPage} />
                <Route path="/profile" component={ProfileSettingsPage} />
                <Route path="/llm" component={LLMSettingsPage} />
                <Route path="/notifications" component={NotificationConfigPage} />
                <Route path="/notifications/push" component={PushSubscriptionsPage} />
                <Route path="/notifications/push/:id" component={PushSubscriptionDetailPage} />
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
                <Route
                  path="/routine-definitions"
                  component={RoutineDefinitionsPage}
                />
                <Route
                  path="/routine-definitions/new"
                  component={NewRoutineDefinitionPage}
                />
                <Route
                  path="/routine-definitions/:id"
                  component={RoutineDefinitionDetailPage}
                />
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
              </Route>
            </Route>

            <Route path="*" component={NotFound} />
          </Router>
        </div>
      </div>
    </NotificationProvider>
  );
}
