import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { BrainDumpItem, BrainDumpItemStatus } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streaming-data";
import { SwipeableItem } from "@/components/shared/SwipeableItem";

const getStatusClasses = (status: BrainDumpItemStatus): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-stone-50/50";
    case "PUNT":
      return "bg-amber-50/30 italic";
    default:
      return "";
  }
};

const BrainDumpItemRow: Component<{ item: BrainDumpItem }> = (props) => {
  const { updateBrainDumpItemStatus, removeBrainDumpItem } = useStreamingData();

  const handleSwipeLeft = () => {
    if (props.item.status === "COMPLETE") {
      removeBrainDumpItem(props.item.id);
    } else {
      updateBrainDumpItemStatus(props.item, "PUNT");
    }
  };

  return (
    <SwipeableItem
      onSwipeRight={() => updateBrainDumpItemStatus(props.item, "COMPLETE")}
      onSwipeLeft={handleSwipeLeft}
      rightLabel="✅ Complete"
      leftLabel={props.item.status === "COMPLETE" ? "🗑 Remove" : "⏸ Punt"}
      statusClass={getStatusClasses(props.item.status)}
      compact={true}
    >
      <div class="flex items-center gap-4">
        <span class="w-4 flex-shrink-0 flex items-center justify-center text-sky-600">
          <span class="text-lg">🧠</span>
        </span>

        <div class="flex-1 min-w-0">
          <span
            class={`text-sm truncate block ${
              props.item.status === "COMPLETE"
                ? "line-through text-stone-400"
                : "text-stone-800"
            }`}
          >
            {props.item.text}
          </span>
        </div>

        <Show when={props.item.status === "COMPLETE"}>
          <div class="flex-shrink-0 w-4 text-sky-600">
            <Icon key="checkMark" />
          </div>
        </Show>
      </div>
    </SwipeableItem>
  );
};

interface BrainDumpListProps {
  items: Accessor<BrainDumpItem[]>;
}

const BrainDumpList: Component<BrainDumpListProps> = (props) => {
  const items = () => props.items() ?? [];

  return (
    <>
      <For each={items()}>{(item) => <BrainDumpItemRow item={item} />}</For>
    </>
  );
};

export default BrainDumpList;
