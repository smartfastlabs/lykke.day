import { useNavigate } from "@solidjs/router";
import { Component, Show, onMount } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import SettingsList from "@/components/shared/SettingsList";
import TodayNotificationListItem from "@/components/notifications/TodayNotificationListItem";
import { useStreamingData } from "@/providers/streamingData";
import { PushNotification } from "@/types/api";

const getNotificationLabel = (notification: PushNotification): string => {
  if (notification.message) return notification.message;
  try {
    const parsed = JSON.parse(notification.content);
    if (parsed && typeof parsed === "object") {
      const title = (parsed as { title?: string }).title;
      if (title) return title;
    }
  } catch {
    return notification.status;
  }
  return notification.status;
};

const TodayNotificationsPage: Component = () => {
  const navigate = useNavigate();
  const { notifications, notificationsLoading, loadNotifications } = useStreamingData();

  onMount(() => {
    void loadNotifications();
  });

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/notifications/${id}`);
  };

  return (
    <SettingsPage heading="Today's Notifications">
      <Show
        when={!notificationsLoading() || notifications().length > 0}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <SettingsList
          items={notifications()}
          getItemLabel={getNotificationLabel}
          renderItem={(notification) => (
            <TodayNotificationListItem notification={notification} />
          )}
          onItemClick={(notification) => handleNavigate(notification.id)}
          searchPlaceholder="Search notifications"
          emptyStateLabel="No notifications sent today."
        />
      </Show>
    </SettingsPage>
  );
};

export default TodayNotificationsPage;
