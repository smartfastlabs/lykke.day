import {
  Component,
  createSignal,
  onMount,
  onCleanup,
  For,
  Show,
} from "solid-js";
import Page from "@/components/shared/layout/Page";
import { Icon } from "solid-heroicons";
import { signal, circleStack } from "solid-heroicons/outline";
import { getWebSocketBaseUrl, getWebSocketProtocol } from "@/utils/config";

interface AuditLog {
  id: string;
  user_id: string;
  activity_type: string;
  occurred_at: string;
  entity_id: string | null;
  entity_type: string | null;
  meta: Record<string, unknown>;
}

interface WebSocketMessage {
  type: string;
  audit_log?: AuditLog;
  user_id?: string;
  code?: string;
  message?: string;
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
};

const formatActivityType = (activityType: string): string => {
  // Convert camelCase/PascalCase to readable format
  return activityType
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

const getActivityColor = (activityType: string): string => {
  if (activityType.includes("Completed") || activityType.includes("Created")) {
    return "from-emerald-500/80 to-green-600/80";
  }
  if (activityType.includes("Deleted") || activityType.includes("Removed")) {
    return "from-red-500/80 to-rose-600/80";
  }
  if (activityType.includes("Updated") || activityType.includes("Modified")) {
    return "from-blue-500/80 to-indigo-600/80";
  }
  return "from-stone-500/80 to-stone-600/80";
};

const EventCard: Component<{ event: AuditLog; index: number }> = (props) => {
  return (
    <div
      class="group bg-white/60 backdrop-blur-sm border border-white/70 rounded-2xl p-6 hover:bg-white/80 hover:shadow-xl hover:shadow-amber-900/10 transition-all duration-300"
      style={{
        animation: `fadeInUp 0.6s ease-out ${props.index * 0.1}s both`,
      }}
    >
      <div class="flex items-start gap-4">
        <div
          class={`flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br ${getActivityColor(props.event.activity_type)} flex items-center justify-center group-hover:scale-105 transition-transform duration-300`}
        >
          <Icon path={circleStack} class="w-6 h-6 text-white" />
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-3 mb-2">
            <h3 class="text-stone-900 font-semibold text-lg leading-snug">
              {formatActivityType(props.event.activity_type)}
            </h3>
            <span class="flex-shrink-0 text-xs text-stone-500">
              {formatTimestamp(props.event.occurred_at)}
            </span>
          </div>

          <Show when={props.event.entity_type || props.event.entity_id}>
            <div class="flex flex-wrap items-center gap-3 text-sm text-stone-600 mb-2">
              <Show when={props.event.entity_type}>
                <span class="px-2.5 py-1 bg-stone-100 rounded-full text-stone-700 font-medium">
                  {props.event.entity_type}
                </span>
              </Show>
              <Show when={props.event.entity_id}>
                <span class="text-stone-500 font-mono text-xs">
                  {props.event.entity_id?.substring(0, 8)}...
                </span>
              </Show>
            </div>
          </Show>

          <Show when={Object.keys(props.event.meta).length > 0}>
            <div class="mt-3 p-3 bg-stone-50 rounded-lg border border-stone-200">
              <pre class="text-xs text-stone-600 overflow-x-auto">
                {JSON.stringify(props.event.meta, null, 2)}
              </pre>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
};

const ConnectionStatus: Component<{
  status: "connecting" | "connected" | "disconnected";
}> = (props) => {
  const statusConfig = {
    connecting: {
      text: "Connecting...",
      color: "text-amber-600",
      bg: "bg-amber-50",
      icon: signal,
    },
    connected: {
      text: "Connected",
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      icon: signal,
    },
    disconnected: {
      text: "Disconnected",
      color: "text-red-600",
      bg: "bg-red-50",
      icon: signal,
    },
  };

  const config = () => statusConfig[props.status];

  return (
    <div
      class={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${config().bg} ${config().color} text-sm font-medium`}
    >
      <Icon path={config().icon} class="w-4 h-4" />
      <span>{config().text}</span>
    </div>
  );
};

export const EventsPage: Component = () => {
  const [events, setEvents] = createSignal<AuditLog[]>([]);
  const [connectionStatus, setConnectionStatus] = createSignal<
    "connecting" | "connected" | "disconnected"
  >("disconnected");
  const [error, setError] = createSignal<string | null>(null);

  let ws: WebSocket | null = null;

  const connectWebSocket = () => {
    setConnectionStatus("connecting");
    setError(null);

    // Get WebSocket configuration
    const protocol = getWebSocketProtocol();
    const baseUrl = getWebSocketBaseUrl();

    // Get auth token from cookie (same cookie used for API requests)
    const getCookie = (name: string): string | null => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
      return null;
    };

    const token = getCookie("lykke_auth");

    // Build WebSocket URL with token as query parameter if available
    // API_PREFIX is empty, so route is at /events/ws
    let wsUrl = `${protocol}//${baseUrl}/events/ws`;
    if (token) {
      wsUrl += `?token=${encodeURIComponent(token)}`;
    }

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionStatus("connected");
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "connection_ack") {
            console.log("WebSocket connected for user:", message.user_id);
          } else if (message.type === "audit_log_event" && message.audit_log) {
            // Add new event to the beginning of the list
            setEvents((prev) => [message.audit_log!, ...prev]);
          } else if (message.type === "error") {
            setError(message.message || "Unknown error");
            console.error("WebSocket error:", message.code, message.message);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setError("Connection error occurred");
        setConnectionStatus("disconnected");
      };

      ws.onclose = () => {
        setConnectionStatus("disconnected");
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (connectionStatus() !== "connected") {
            connectWebSocket();
          }
        }, 3000);
      };
    } catch (err) {
      console.error("Error creating WebSocket:", err);
      setError("Failed to create WebSocket connection");
      setConnectionStatus("disconnected");
    }
  };

  onMount(() => {
    connectWebSocket();
  });

  onCleanup(() => {
    if (ws) {
      ws.close();
    }
  });

  return (
    <Page>
      <div class="min-h-screen relative overflow-hidden">
        <div class="relative z-10 max-w-4xl mx-auto px-6 py-8 md:py-12">
          {/* Header */}
          <div class="mb-8 flex items-center justify-between">
            <div>
              <h1 class="text-2xl md:text-3xl font-bold text-stone-800 mb-2">
                Audit Log Events
              </h1>
              <p class="text-stone-600">
                Live stream of all system events and activities
              </p>
            </div>
            <ConnectionStatus status={connectionStatus()} />
          </div>

          {/* Error message */}
          <Show when={error()}>
            <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
              {error()}
            </div>
          </Show>

          {/* Events list */}
          <Show
            when={events().length > 0}
            fallback={
              <div class="text-center py-16">
                <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
                  <Icon path={circleStack} class="w-10 h-10 text-amber-700" />
                </div>
                <h3 class="text-xl font-semibold text-stone-800 mb-2">
                  No events yet
                </h3>
                <p class="text-stone-600">
                  {connectionStatus() === "connected"
                    ? "Events will appear here as they occur"
                    : "Waiting for connection..."}
                </p>
              </div>
            }
          >
            <div class="space-y-3">
              <For each={events()}>
                {(event, index) => <EventCard event={event} index={index()} />}
              </For>
            </div>
          </Show>

          {/* Animation styles */}
          <style>{`
            @keyframes fadeInUp {
              from {
                opacity: 0;
                transform: translateY(20px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
          `}</style>
        </div>
      </div>
    </Page>
  );
};

export default EventsPage;
