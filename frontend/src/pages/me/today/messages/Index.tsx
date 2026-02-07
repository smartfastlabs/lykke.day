import { useNavigate } from "@solidjs/router";
import { Component, Show, onMount } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import SettingsList from "@/components/shared/SettingsList";
import TodayMessageListItem from "@/components/messages/TodayMessageListItem";
import { useStreamingData } from "@/providers/streamingData";
import type { Message } from "@/types/api";

const getMessageLabel = (message: Message): string => {
  return message.content || "";
};

const TodayMessagesPage: Component = () => {
  const navigate = useNavigate();
  const { messages, messagesLoading, loadMessages } = useStreamingData();

  onMount(() => {
    void loadMessages();
  });

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/messages/${id}`);
  };

  return (
    <SettingsPage heading="Today's Messages">
      <Show
        when={!messagesLoading() || messages().length > 0}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <SettingsList
          items={messages()}
          getItemLabel={getMessageLabel}
          renderItem={(message) => <TodayMessageListItem message={message} />}
          onItemClick={(message) => handleNavigate(message.id)}
          searchPlaceholder="Search messages"
          emptyStateLabel="No messages created today."
        />
      </Show>
    </SettingsPage>
  );
};

export default TodayMessagesPage;
