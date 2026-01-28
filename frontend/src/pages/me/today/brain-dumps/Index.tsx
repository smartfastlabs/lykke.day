import { useNavigate } from "@solidjs/router";
import { Component, Show } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import SettingsList from "@/components/shared/SettingsList";
import TodayBrainDumpListItem from "@/components/brain-dump/TodayBrainDumpListItem";
import { useStreamingData } from "@/providers/streamingData";
import type { BrainDump } from "@/types/api";

const getBrainDumpLabel = (item: BrainDump): string =>
  item.text.trim() || item.status;

const TodayBrainDumpsPage: Component = () => {
  const navigate = useNavigate();
  const { brainDumps, isLoading } = useStreamingData();

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/brain-dumps/${id}`);
  };

  return (
    <SettingsPage heading="Today's Brain Dumps">
      <Show
        when={!isLoading() || brainDumps().length > 0}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <SettingsList
          items={brainDumps()}
          getItemLabel={getBrainDumpLabel}
          renderItem={(item) => <TodayBrainDumpListItem item={item} />}
          onItemClick={(item) => handleNavigate(item.id)}
          searchPlaceholder="Search brain dumps"
          emptyStateLabel="No brain dumps captured today."
        />
      </Show>
    </SettingsPage>
  );
};

export default TodayBrainDumpsPage;
