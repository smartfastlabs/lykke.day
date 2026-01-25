import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import SettingsList from "@/components/shared/SettingsList";
import TodayBrainDumpListItem from "@/components/brain-dump/TodayBrainDumpListItem";
import { brainDumpAPI } from "@/utils/api";
import type { BrainDumpItem } from "@/types/api";

const getBrainDumpLabel = (item: BrainDumpItem): string =>
  item.text.trim() || item.status;

const TodayBrainDumpsPage: Component = () => {
  const navigate = useNavigate();
  const [brainDumps] = createResource(brainDumpAPI.getToday);

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/brain-dumps/${id}`);
  };

  return (
    <SettingsPage heading="Today's Brain Dumps">
      <Show
        when={brainDumps()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <SettingsList
          items={brainDumps()!}
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
