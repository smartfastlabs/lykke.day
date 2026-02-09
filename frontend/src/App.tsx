import { Title, MetaProvider } from "@solidjs/meta";
import {
  Navigate,
  Route,
  Router,
  useLocation,
  useNavigate,
} from "@solidjs/router";
import { createEffect, onCleanup, onMount } from "solid-js";
import "@/index.css";

import { NotificationProvider } from "@/providers/notifications";
import { LoadingIndicator, LoadingProvider } from "@/providers/loading";
import { AuthProvider } from "@/providers/auth";
import { AuthGuard } from "@/providers/authGuard";
import { AdminGuard } from "@/providers/adminGuard";
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
import TodayIndexView from "@/pages/me/today/Index";
import TasksView from "@/pages/me/today/Tasks";
import EventsView from "@/pages/me/today/Events";
import AlarmsView from "@/pages/me/today/Alarms";
import RemindersView from "@/pages/me/today/Reminders";
import RoutinesView from "@/pages/me/today/Routines";
import TomorrowLayout from "@/pages/me/tomorrow/Layout";
import TomorrowPreviewView from "@/pages/me/tomorrow/Preview";
import TomorrowAddReminderPage from "@/pages/me/tomorrow/AddReminder";
import TomorrowAddAdhocTaskPage from "@/pages/me/tomorrow/AddAdhocTask";
import TomorrowAddAlarmPage from "@/pages/me/tomorrow/AddAlarm";
import TomorrowRoutinesView from "@/pages/me/tomorrow/Routines";
import TodayNotificationsPage from "@/pages/me/today/notifications/Index";
import TodayNotificationDetailPage from "@/pages/me/today/notifications/Detail";
import TodayMessagesPage from "@/pages/me/today/messages/Index";
import TodayMessageDetailPage from "@/pages/me/today/messages/Detail";
import TodayBrainDumpsPage from "@/pages/me/today/brain-dumps/Index";
import TodayBrainDumpDetailPage from "@/pages/me/today/brain-dumps/Detail";
import TodayEditPage from "@/pages/me/today/Edit";
import ThatsAllPage from "@/pages/me/today/ThatsAll";
import AddAdhocTaskPage from "@/pages/me/today/AddAdhocTask";
import AddReminderPage from "@/pages/me/today/AddReminder";
import AddAlarmPage from "@/pages/me/today/AddAlarm";
import MeIndexPage from "@/pages/me/Index";
import BrainDumpPage from "@/pages/me/BrainDump";
import KioskPage from "@/pages/me/kiosk/Index";
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
import MorningOverviewConfigPage from "@/pages/me/settings/morning/Index";
import MessagingConfigPage from "@/pages/me/settings/messaging/Index";
import AlarmPresetsPage from "@/pages/me/settings/alarms/Index";
import CalendarNotificationsPage from "@/pages/me/settings/calendar-notifications/Index";
import TaskDefinitionsPage from "@/pages/me/settings/task-definitions/Index";
import NewTaskDefinitionPage from "@/pages/me/settings/task-definitions/New";
import TaskDefinitionDetailPage from "@/pages/me/settings/task-definitions/Detail";
import RoutineDefinitionsPage from "@/pages/me/settings/routine-definitions/Index";
import NewRoutineDefinitionPage from "@/pages/me/settings/routine-definitions/New";
import RoutineDefinitionDetailPage from "@/pages/me/settings/routine-definitions/Detail";
import FactoidsPage from "@/pages/me/settings/factoids/Index";
import NewFactoidPage from "@/pages/me/settings/factoids/New";
import FactoidDetailPage from "@/pages/me/settings/factoids/Detail";
import TimeBlocksPage from "@/pages/me/settings/time-blocks/Index";
import NewTimeBlockPage from "@/pages/me/settings/time-blocks/New";
import TimeBlockDetailPage from "@/pages/me/settings/time-blocks/Detail";
import TacticsPage from "@/pages/me/settings/tactics/Index";
import NewTacticPage from "@/pages/me/settings/tactics/New";
import TacticDetailPage from "@/pages/me/settings/tactics/Detail";
import TriggersPage from "@/pages/me/settings/triggers/Index";
import NewTriggerPage from "@/pages/me/settings/triggers/New";
import TriggerDetailPage from "@/pages/me/settings/triggers/Detail";
import CalendarsPage from "@/pages/me/settings/calendars/Index";
import CalendarDetailPage from "@/pages/me/settings/calendars/Detail";
import RecurringEventsPage from "@/pages/me/settings/recurring-events/Index";
import RecurringEventSeriesDetailPage from "@/pages/me/settings/recurring-events/Detail";
import CalendarRecurringEventsPage from "@/pages/me/settings/calendars/RecurringEvents";
import PushSubscriptionsPage from "@/pages/me/settings/push-subscriptions/Index";
import PushSubscriptionDetailPage from "@/pages/me/settings/push-subscriptions/Detail";
import AdminLayout from "@/pages/admin/Layout";
import AdminIndexPage from "@/pages/admin/Index";
import DomainEventsPage from "@/pages/admin/DomainEvents";
import StreamingSyncPage from "@/pages/admin/Sync";
import NotFound from "@/pages/NotFound";

import "@/utils/icons";

function NavigationHandler() {
  const navigate = useNavigate();
  const location = useLocation();

  const isStandalonePwa = (): boolean => {
    if (typeof window === "undefined") return false;
    const nav = window.navigator as typeof window.navigator & {
      standalone?: boolean;
    };
    return (
      window.matchMedia?.("(display-mode: standalone)")?.matches === true ||
      nav.standalone === true
    );
  };

  const LAST_ME_PATH_KEY = "lykke:last-me-path";

  const persistablePath = (): string =>
    `${location.pathname}${location.search}${location.hash}`;

  const shouldPersistMePath = (path: string): boolean => {
    if (!path.startsWith("/me")) return false;
    if (path === "/me" || path === "/me/") return false;
    return true;
  };

  const getLastMePath = (): string | null => {
    if (typeof window === "undefined") return null;
    try {
      const value = window.localStorage.getItem(LAST_ME_PATH_KEY);
      if (!value) return null;
      if (!value.startsWith("/me")) return null;
      if (value === "/me" || value === "/me/") return null;
      return value;
    } catch {
      return null;
    }
  };

  // Persist last visited /me page (used for PWA resume and /me entry redirect).
  createEffect(() => {
    if (typeof window === "undefined") return;
    const path = persistablePath();
    if (!shouldPersistMePath(path)) return;
    // On older PWA installs the manifest start_url was /me/today. When launching
    // standalone, don't overwrite an existing "last path" with the start_url
    // before we've had a chance to restore it.
    if (isStandalonePwa() && location.pathname === "/me/today") {
      const existing = getLastMePath();
      if (existing && existing !== path) {
        return;
      }
    }
    try {
      window.localStorage.setItem(LAST_ME_PATH_KEY, path);
    } catch {
      // ignore storage failures (private mode, quota, etc.)
    }
  });

  onMount(() => {
    // If the PWA was launched at the manifest start_url (older installs used
    // /me/today), restore the last open /me page instead.
    if (isStandalonePwa() && location.pathname === "/me/today") {
      const last = getLastMePath();
      const current = persistablePath();
      if (last && last !== current) {
        navigate(last, { replace: true });
      }
    }

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
      <LoadingProvider>
        <div
          class="min-h-screen relative overflow-hidden"
          style={{ "min-height": "100dvh" }}
        >
          <LoadingIndicator />
          {/* Background gradients - use fixed positioning to cover entire viewport including notch */}
          <div
            class="fixed inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50"
            style={{ top: "0", left: "0", right: "0", bottom: "0" }}
          />
          <div
            class="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]"
            style={{ top: "0", left: "0", right: "0", bottom: "0" }}
          />
          <div
            class="fixed inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]"
            style={{ top: "0", left: "0", right: "0", bottom: "0" }}
          />

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
              "padding-bottom": "env(safe-area-inset-bottom)",
            }}
          >
            <Router
              root={(props) => (
                <AuthProvider>
                  <NavigationHandler />
                  <MetaProvider>
                    <Title>lykke.day</Title>
                    {props.children}
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
                <Route path="/" component={MeIndexPage} />
                <Route path="/today/kiosk" component={KioskPage} />
                <Route path="/brain-dump" component={BrainDumpPage} />
                <Route path="/adhoc-task" component={AddAdhocTaskPage} />
                <Route path="/add-alarm" component={AddAlarmPage} />
                <Route path="/add-reminder" component={AddReminderPage} />
                <Route
                  path="/tasks"
                  component={() => <Navigate href="/me/today/tasks" />}
                />
                <Route path="/tomorrow" component={TomorrowLayout}>
                  <Route path="/" component={TomorrowPreviewView} />
                  <Route path="/routines" component={TomorrowRoutinesView} />
                </Route>
                <Route
                  path="/tomorrow/add-reminder"
                  component={TomorrowAddReminderPage}
                />
                <Route
                  path="/tomorrow/adhoc-task"
                  component={TomorrowAddAdhocTaskPage}
                />
                <Route
                  path="/tomorrow/add-alarm"
                  component={TomorrowAddAlarmPage}
                />
                <Route path="/thats-all-for-today" component={ThatsAllPage} />
                <Route
                  path="/notifications/:id"
                  component={TodayNotificationDetailPage}
                />
                <Route
                  path="/messages/:id"
                  component={TodayMessageDetailPage}
                />
                <Route
                  path="/brain-dumps/:id"
                  component={TodayBrainDumpDetailPage}
                />
                <Route path="/today" component={HomeLayout}>
                  <Route path="/" component={TodayIndexView} />
                  <Route path="/tasks" component={TasksView} />
                  <Route path="/events" component={EventsView} />
                  <Route path="/alarms" component={AlarmsView} />
                  <Route path="/reminders" component={RemindersView} />
                  <Route path="/routines" component={RoutinesView} />
                  <Route path="/brain-dumps" component={TodayBrainDumpsPage} />
                  <Route
                    path="/notifications"
                    component={TodayNotificationsPage}
                  />
                  <Route path="/messages" component={TodayMessagesPage} />
                  <Route path="/edit" component={TodayEditPage} />
                </Route>
                <Route path="/nav" component={NavigationLayout}>
                  <Route path="/" component={NavPage} />
                  <Route path="/calendar" component={CalendarPage} />
                  <Route path="/commands" component={CommandsPage} />
                </Route>
                <Route path="/admin" component={AdminGuard}>
                  <Route path="/" component={AdminLayout}>
                    <Route path="/" component={AdminIndexPage} />
                    <Route path="/events" component={DomainEventsPage} />
                    <Route path="/sync" component={StreamingSyncPage} />
                  </Route>
                </Route>
                <Route path="/settings" component={SettingsLayout}>
                  <Route path="/" component={SettingsIndexPage} />
                  <Route path="/profile" component={ProfileSettingsPage} />
                  <Route path="/llm" component={LLMSettingsPage} />
                  <Route
                    path="/notifications"
                    component={NotificationConfigPage}
                  />
                  <Route
                    path="/calendar-notifications"
                    component={CalendarNotificationsPage}
                  />
                  <Route
                    path="/morning"
                    component={MorningOverviewConfigPage}
                  />
                  <Route path="/messaging" component={MessagingConfigPage} />
                  <Route path="/alarms" component={AlarmPresetsPage} />
                  <Route
                    path="/notifications/push"
                    component={PushSubscriptionsPage}
                  />
                  <Route
                    path="/notifications/push/:id"
                    component={PushSubscriptionDetailPage}
                  />
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
                  <Route path="/factoids" component={FactoidsPage} />
                  <Route path="/factoids/new" component={NewFactoidPage} />
                  <Route path="/factoids/:id" component={FactoidDetailPage} />
                  <Route path="/triggers" component={TriggersPage} />
                  <Route path="/triggers/new" component={NewTriggerPage} />
                  <Route path="/triggers/:id" component={TriggerDetailPage} />
                  <Route path="/tactics" component={TacticsPage} />
                  <Route path="/tactics/new" component={NewTacticPage} />
                  <Route path="/tactics/:id" component={TacticDetailPage} />
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

              <Route
                path="/admin"
                component={() => <Navigate href="/me/admin" />}
              />
              <Route
                path="/admin/*all"
                component={(props) => (
                  <Navigate href={`/me/admin/${props.params.all}`} />
                )}
              />

              <Route path="*" component={NotFound} />
            </Router>
          </div>
        </div>
      </LoadingProvider>
    </NotificationProvider>
  );
}
