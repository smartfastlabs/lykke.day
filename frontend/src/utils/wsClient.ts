export interface DomainEventEnvelope {
  event_type: string;
  event_data: Record<string, unknown>;
}

export type JsonObject = Record<string, unknown>;

interface TopicEventMessage<TTopicEvent> {
  type: "topic_event";
  topic: string;
  event: TTopicEvent;
}

interface SubscriptionMessage {
  type: "subscribe" | "unsubscribe";
  topics: string[];
}

const isJsonObject = (value: unknown): value is JsonObject =>
  typeof value === "object" && value !== null;

const isTopicEventMessage = <TTopicEvent>(
  value: unknown,
): value is TopicEventMessage<TTopicEvent> => {
  if (!isJsonObject(value)) return false;
  return (
    value.type === "topic_event" &&
    typeof value.topic === "string" &&
    "event" in value
  );
};

export interface WsClient<TTopicEvent = DomainEventEnvelope> {
  connect: () => void;
  close: () => void;
  isOpen: () => boolean;
  sendJson: (message: unknown) => boolean;
  subscribeTopic: (
    topic: string,
    handler: (event: TTopicEvent) => void,
  ) => () => void;
  unsubscribeTopic: (topic: string) => void;
}

export interface CreateWsClientOptions<TInboundMessage = unknown> {
  url: string;
  reconnectDelayMs?: number;
  shouldReconnect?: () => boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (event: Event) => void;
  onMessage?: (message: TInboundMessage) => void | Promise<void>;
  onParseError?: (error: unknown) => void;
  onProtocolError?: (message: unknown) => void;
  logger?: Pick<typeof console, "log" | "warn" | "error">;
}

export const createWsClient = <
  TInboundMessage = unknown,
  TTopicEvent = DomainEventEnvelope,
>(
  options: CreateWsClientOptions<TInboundMessage>,
): WsClient<TTopicEvent> => {
  const reconnectDelayMs = options.reconnectDelayMs ?? 3000;
  const shouldReconnect = options.shouldReconnect ?? (() => true);
  const logger = options.logger ?? console;

  let ws: WebSocket | null = null;
  let reconnectTimeout: number | null = null;

  const subscribedTopics = new Set<string>();
  const topicHandlers = new Map<string, Set<(event: TTopicEvent) => void>>();

  const isOpen = (): boolean => Boolean(ws && ws.readyState === WebSocket.OPEN);

  const clearReconnectTimer = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
  };

  const sendJson = (message: unknown): boolean => {
    if (!isOpen() || !ws) return false;
    ws.send(JSON.stringify(message));
    return true;
  };

  const sendSubscriptionUpdate = (
    type: SubscriptionMessage["type"],
    topics: string[],
  ) => {
    if (topics.length === 0) return;
    sendJson({ type, topics } satisfies SubscriptionMessage);
  };

  const handleParsedMessage = async (message: unknown) => {
    if (isTopicEventMessage<TTopicEvent>(message)) {
      const handlers = topicHandlers.get(message.topic);
      if (!handlers || handlers.size === 0) return;
      handlers.forEach((handler) => handler(message.event));
      return;
    }

    if (options.onMessage) {
      await options.onMessage(message as TInboundMessage);
    }
  };

  const connect = () => {
    clearReconnectTimer();

    try {
      ws = new WebSocket(options.url);

      ws.onopen = () => {
        options.onOpen?.();
        if (subscribedTopics.size > 0) {
          sendSubscriptionUpdate("subscribe", Array.from(subscribedTopics));
        }
      };

      ws.onmessage = async (event) => {
        try {
          const parsed = JSON.parse(event.data as string) as unknown;
          await handleParsedMessage(parsed);
        } catch (error) {
          options.onParseError?.(error);
          logger.error("wsClient: failed to parse message", error);
        }
      };

      ws.onerror = (event) => {
        options.onError?.(event);
      };

      ws.onclose = () => {
        options.onClose?.();
        ws = null;

        if (!shouldReconnect()) return;

        clearReconnectTimer();
        reconnectTimeout = window.setTimeout(() => {
          if (!shouldReconnect()) return;
          connect();
        }, reconnectDelayMs);
      };
    } catch (error) {
      options.onProtocolError?.(error);
      logger.error("wsClient: failed to create WebSocket", error);
    }
  };

  const close = () => {
    clearReconnectTimer();
    if (ws) {
      ws.close();
    }
    ws = null;
  };

  const subscribeTopic = (
    topic: string,
    handler: (event: TTopicEvent) => void,
  ) => {
    const handlers = topicHandlers.get(topic) ?? new Set();
    handlers.add(handler);
    topicHandlers.set(topic, handlers);

    if (!subscribedTopics.has(topic)) {
      subscribedTopics.add(topic);
      sendSubscriptionUpdate("subscribe", [topic]);
    }

    return () => {
      const currentHandlers = topicHandlers.get(topic);
      if (!currentHandlers) return;

      currentHandlers.delete(handler);
      if (currentHandlers.size === 0) {
        topicHandlers.delete(topic);
        subscribedTopics.delete(topic);
        sendSubscriptionUpdate("unsubscribe", [topic]);
      } else {
        topicHandlers.set(topic, currentHandlers);
      }
    };
  };

  const unsubscribeTopic = (topic: string) => {
    topicHandlers.delete(topic);
    if (!subscribedTopics.has(topic)) return;
    subscribedTopics.delete(topic);
    sendSubscriptionUpdate("unsubscribe", [topic]);
  };

  return {
    connect,
    close,
    isOpen,
    sendJson,
    subscribeTopic,
    unsubscribeTopic,
  };
};
