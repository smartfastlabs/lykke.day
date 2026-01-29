import {
  Component,
  For,
  Show,
  createSignal,
  createResource,
  onMount,
  onCleanup,
  createMemo,
} from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { adminAPI, DomainEventItem, DomainEventFilters } from "@/utils/api";
import { getWebSocketBaseUrl, getWebSocketProtocol } from "@/utils/config";

function getCookie(name: string): string | undefined {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(";").shift();
  return undefined;
}

function formatEventType(eventType: string): string {
  const parts = eventType.split(".");
  return parts[parts.length - 1];
}

/** Map event type (short name) to a cluster for filtering. */
function getEventCluster(eventType: string): string {
  const short = formatEventType(eventType);
  const lower = short.toLowerCase();
  if (short === "TaskIQRun" || lower.startsWith("taskiq")) return "TaskIQ";
  if (short === "LLMUsecaseRun" || lower.includes("llm")) return "LLM";
  if (lower.startsWith("task")) return "Task";
  if (lower.startsWith("braindump")) return "Brain dump";
  if (lower.startsWith("day")) return "Day";
  if (lower.startsWith("reminder")) return "Reminder";
  if (lower.startsWith("alarm")) return "Alarm";
  if (lower.includes("calendar")) return "Calendar";
  if (lower.startsWith("routine")) return "Routine";
  if (lower.startsWith("entity")) return "Entity";
  if (lower.startsWith("message")) return "Message";
  if (lower.startsWith("kiosk")) return "Notification";
  if (lower.startsWith("factoid")) return "Factoid";
  if (lower.startsWith("trigger") || lower.startsWith("tactic"))
    return "Trigger/Tactic";
  if (lower.startsWith("user")) return "User";
  if (lower.startsWith("conversation")) return "Chat";
  return "Other";
}

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString();
}

const EventsPage: Component = () => {
  const [filters, setFilters] = createSignal<DomainEventFilters>({
    limit: 100,
    offset: 0,
  });
  const [searchText, setSearchText] = createSignal("");
  const [userIdFilter, setUserIdFilter] = createSignal("");
  const [eventTypeFilter, setEventTypeFilter] = createSignal("");
  const [realtimeEvents, setRealtimeEvents] = createSignal<DomainEventItem[]>(
    [],
  );
  const [expandedEvents, setExpandedEvents] = createSignal<Set<string>>(
    new Set(),
  );
  const [hiddenClusters, setHiddenClusters] = createSignal<Set<string>>(
    new Set(),
  );
  const [isConnected, setIsConnected] = createSignal(false);
  const [isStreaming, setIsStreaming] = createSignal(true);

  const [events] = createResource(filters, async (f) => {
    const result = await adminAPI.getDomainEvents(f);
    return result;
  });

  let ws: WebSocket | null = null;

  const connectWebSocket = () => {
    const protocol = getWebSocketProtocol();
    const baseUrl = getWebSocketBaseUrl();
    const token = getCookie("lykke_auth");

    // Build WebSocket URL - same pattern as days websocket
    let wsUrl = `${protocol}//${baseUrl}/admin/events/stream`;
    if (token) {
      wsUrl += `?token=${encodeURIComponent(token)}`;
    }
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "domain_event" && isStreaming()) {
          const newEvent = message.data as DomainEventItem;
          setRealtimeEvents((prev) => [newEvent, ...prev].slice(0, 100));
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (isStreaming()) {
          connectWebSocket();
        }
      }, 3000);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };
  };

  onMount(() => {
    connectWebSocket();
  });

  onCleanup(() => {
    if (ws) {
      ws.close();
    }
  });

  const allEvents = createMemo(() => {
    const historical = events()?.items ?? [];
    const realtime = realtimeEvents();
    const seen = new Set<string>();
    const combined: DomainEventItem[] = [];
    for (const e of [...realtime, ...historical]) {
      if (!seen.has(e.id)) {
        seen.add(e.id);
        combined.push(e);
      }
    }
    return combined;
  });

  const clusterCounts = createMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of allEvents()) {
      const cluster = getEventCluster(e.event_type);
      counts[cluster] = (counts[cluster] ?? 0) + 1;
    }
    return counts;
  });

  const visibleEvents = createMemo(() => {
    const hidden = hiddenClusters();
    return allEvents().filter(
      (e) => !hidden.has(getEventCluster(e.event_type)),
    );
  });

  const toggleClusterVisibility = (cluster: string) => {
    setHiddenClusters((prev) => {
      const next = new Set(prev);
      if (next.has(cluster)) {
        next.delete(cluster);
      } else {
        next.add(cluster);
      }
      return next;
    });
  };

  const toggleExpanded = (id: string) => {
    setExpandedEvents((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const applyFilters = () => {
    setRealtimeEvents([]);
    setFilters((f) => ({
      ...f,
      search: searchText() || undefined,
      user_id: userIdFilter() || undefined,
      event_type: eventTypeFilter() || undefined,
      offset: 0,
    }));
  };

  const clearFilters = () => {
    setSearchText("");
    setUserIdFilter("");
    setEventTypeFilter("");
    setRealtimeEvents([]);
    setFilters({ limit: 100, offset: 0 });
  };

  const goToPage = (newOffset: number) => {
    setFilters((f) => ({ ...f, offset: newOffset }));
  };

  return (
    <SettingsPage heading="Events">
      {/* Connection Status */}
      <div class="mb-4 flex items-center gap-4">
        <div class="flex items-center gap-2">
          <div
            class={`w-2 h-2 rounded-full ${isConnected() ? "bg-green-500" : "bg-red-500"}`}
          />
          <span class="text-sm text-gray-600">
            {isConnected() ? "Connected" : "Disconnected"}
          </span>
        </div>
        <button
          class={`px-3 py-1 text-sm rounded-full border transition-all ${
            isStreaming()
              ? "bg-amber-100 text-amber-700 border-amber-200"
              : "bg-gray-100 text-gray-600 border-gray-200"
          }`}
          onClick={() => setIsStreaming(!isStreaming())}
        >
          {isStreaming() ? "Streaming" : "Paused"}
        </button>
        <Show when={realtimeEvents().length > 0}>
          <span class="text-xs text-gray-500">
            +{realtimeEvents().length} new
          </span>
        </Show>
      </div>

      {/* Search and Filters */}
      <div class="mb-6 space-y-4 p-4 bg-gray-50 rounded-lg">
        <div class="flex gap-4">
          <input
            type="text"
            placeholder="Search events..."
            value={searchText()}
            onInput={(e) => setSearchText(e.currentTarget.value)}
            class="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-200"
          />
          <button
            onClick={applyFilters}
            class="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
          >
            Search
          </button>
          <button
            onClick={clearFilters}
            class="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Clear
          </button>
        </div>

        <div class="flex flex-wrap gap-4">
          <div class="flex-1 min-w-48">
            <label class="block text-xs uppercase tracking-wider text-gray-400 mb-1">
              User ID
            </label>
            <input
              type="text"
              placeholder="Filter by user ID..."
              value={userIdFilter()}
              onInput={(e) => setUserIdFilter(e.currentTarget.value)}
              class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-amber-200"
            />
          </div>
          <div class="flex-1 min-w-48">
            <label class="block text-xs uppercase tracking-wider text-gray-400 mb-1">
              Event Type
            </label>
            <input
              type="text"
              placeholder="e.g., TaskCompleted..."
              value={eventTypeFilter()}
              onInput={(e) => setEventTypeFilter(e.currentTarget.value)}
              class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-amber-200"
            />
          </div>
        </div>
      </div>

      {/* Cluster filters: show/hide by category */}
      <Show when={Object.keys(clusterCounts()).length > 0}>
        <div class="mb-4 flex flex-wrap items-center gap-2">
          <span class="text-xs uppercase tracking-wider text-gray-400 mr-1">
            Show / hide:
          </span>
          <Show when={hiddenClusters().size > 0}>
            <button
              type="button"
              onClick={() => setHiddenClusters(new Set())}
              class="text-xs text-amber-600 hover:text-amber-700 font-medium"
            >
              Show all
            </button>
          </Show>
          <For
            each={Object.entries(clusterCounts()).sort((a, b) =>
              a[0].localeCompare(b[0]),
            )}
          >
            {([cluster, count]) => {
              const isHidden = () => hiddenClusters().has(cluster);
              return (
                <button
                  type="button"
                  onClick={() => toggleClusterVisibility(cluster)}
                  class={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                    isHidden()
                      ? "bg-gray-100 text-gray-400 border border-gray-200 hover:bg-gray-200"
                      : "bg-amber-100 text-amber-800 border border-amber-200 hover:bg-amber-200"
                  }`}
                >
                  {cluster}
                  <span class="text-xs opacity-80">({count})</span>
                </button>
              );
            }}
          </For>
        </div>
      </Show>

      {/* Events List */}
      <div class="space-y-2">
        <Show
          when={!events.loading}
          fallback={
            <div class="text-center text-gray-500 py-8">Loading events...</div>
          }
        >
          <Show
            when={visibleEvents().length > 0}
            fallback={
              <div class="text-center text-gray-500 py-8">
                {allEvents().length > 0
                  ? "No events match the current filters"
                  : "No events found"}
              </div>
            }
          >
            <For each={visibleEvents()}>
              {(event) => (
                <div
                  class="p-4 bg-white rounded-lg shadow-sm border border-gray-100 hover:border-gray-200 transition-colors cursor-pointer"
                  onClick={() => toggleExpanded(event.id)}
                >
                  <div class="flex justify-between items-start">
                    <div class="flex items-center gap-2">
                      <span class="font-mono text-sm text-amber-600 font-medium">
                        {formatEventType(event.event_type)}
                      </span>
                      <Show when={event.event_data.user_id}>
                        <span class="text-xs text-gray-400 font-mono">
                          user:{String(event.event_data.user_id).slice(0, 8)}...
                        </span>
                      </Show>
                    </div>
                    <span class="text-xs text-gray-500">
                      {formatTimestamp(event.stored_at)}
                    </span>
                  </div>
                  <Show when={expandedEvents().has(event.id)}>
                    <div class="mt-3 pt-3 border-t border-gray-100">
                      <div class="text-xs text-gray-400 mb-1">Full Type:</div>
                      <div class="text-xs font-mono text-gray-600 mb-3">
                        {event.event_type}
                      </div>
                      <div class="text-xs text-gray-400 mb-1">Event Data:</div>
                      <pre class="text-xs font-mono text-gray-700 bg-gray-50 p-3 rounded overflow-auto max-h-64">
                        {JSON.stringify(event.event_data, null, 2)}
                      </pre>
                    </div>
                  </Show>
                </div>
              )}
            </For>
          </Show>
        </Show>
      </div>

      {/* Pagination */}
      <Show when={events() && events()!.total > (filters().limit ?? 100)}>
        <div class="mt-6 flex justify-between items-center">
          <button
            disabled={!events()?.has_previous}
            onClick={() =>
              goToPage(
                Math.max(0, (filters().offset ?? 0) - (filters().limit ?? 100)),
              )
            }
            class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors"
          >
            Previous
          </button>
          <span class="text-sm text-gray-600">
            Showing {(filters().offset ?? 0) + 1} -{" "}
            {Math.min(
              (filters().offset ?? 0) + (filters().limit ?? 100),
              events()?.total ?? 0,
            )}{" "}
            of {events()?.total ?? 0}
          </span>
          <button
            disabled={!events()?.has_next}
            onClick={() =>
              goToPage((filters().offset ?? 0) + (filters().limit ?? 100))
            }
            class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors"
          >
            Next
          </button>
        </div>
      </Show>
    </SettingsPage>
  );
};

export default EventsPage;
