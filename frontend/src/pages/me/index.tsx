import { Component, For, createSignal, Show } from "solid-js";
import { A } from "@solidjs/router";
import Page from "@/components/shared/layout/Page";

interface Message {
  id: string;
  from: "assistant" | "user";
  text: string;
  timestamp: string;
}

// Mock data for the chat
const MOCK_MESSAGES: Message[] = [
  {
    id: "1",
    from: "assistant",
    text: "Good morning! Welcome to your personal planning space. I'm here to help you organize your days, set goals, and stay on track.",
    timestamp: "9:15 AM",
  },
  {
    id: "2",
    from: "user",
    text: "Hi! How does this work?",
    timestamp: "9:16 AM",
  },
  {
    id: "3",
    from: "assistant",
    text: "I can help you plan your days, manage tasks, and keep track of events. You can check out your daily overview by clicking the 'Today' link above. Would you like to see what's planned for today?",
    timestamp: "9:16 AM",
  },
  {
    id: "4",
    from: "user",
    text: "Yes, that would be great!",
    timestamp: "9:17 AM",
  },
  {
    id: "5",
    from: "assistant",
    text: "Perfect! I've prepared a detailed view of your day including all your tasks and events. You can also ask me anything about your schedule, goals, or how to best organize your time. I'm here to help you build the life you want, one day at a time.",
    timestamp: "9:17 AM",
  },
];

export const MePage: Component = () => {
  const [messages] = createSignal(MOCK_MESSAGES);
  const [newMessage, setNewMessage] = createSignal("");
  const [showInput, setShowInput] = createSignal(false);

  const handleSendMessage = () => {
    const message = newMessage().trim();
    if (message) {
      // TODO: Send message to backend
      console.log("Sending message:", message);
      setNewMessage("");
      setShowInput(false);
    }
  };

  return (
    <Page>
      <div class="min-h-screen relative overflow-hidden">
        <div class="relative z-10 max-w-4xl mx-auto px-6 py-8 md:py-12">
          {/* Header with link to Today */}
          <div class="mb-8 flex items-center justify-between">
            <h1 class="text-2xl md:text-3xl font-bold text-stone-800">
              Chat with lykke
            </h1>
            <A
              href="/me/today"
              class="px-4 py-2 bg-stone-700 hover:bg-stone-800 text-white text-sm rounded-full transition-colors shadow-sm"
            >
              View Today
            </A>
          </div>

          {/* Chat Messages */}
          <div class="space-y-6 mb-24">
            <For each={messages()}>
              {(message) => (
                <div class="flex items-start gap-3">
                  {/* Avatar */}
                  <div
                    class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-md"
                    classList={{
                      "bg-gradient-to-br from-stone-700 to-stone-800":
                        message.from === "assistant",
                      "bg-stone-300": message.from === "user",
                    }}
                  >
                    <Show
                      when={message.from === "assistant"}
                      fallback={
                        <span class="text-stone-600 text-sm font-semibold">
                          You
                        </span>
                      }
                    >
                      <span class="text-white text-lg">✨</span>
                    </Show>
                  </div>

                  {/* Message Container */}
                  <div class="flex-1 max-w-3xl">
                    {/* Name and timestamp */}
                    <div class="flex items-center gap-2 mb-1.5">
                      <span class="text-sm font-semibold text-stone-700">
                        {message.from === "assistant" ? "lykke" : "You"}
                      </span>
                      <span class="text-xs text-stone-400">
                        {message.timestamp}
                      </span>
                    </div>

                    {/* Message Bubble */}
                    <div
                      class="rounded-2xl shadow-sm"
                      classList={{
                        "bg-stone-100 border border-stone-200 text-stone-800 rounded-tl-sm":
                          message.from === "assistant",
                        "bg-stone-700 text-white rounded-tr-sm":
                          message.from === "user",
                      }}
                    >
                      <div class="p-4">
                        <p
                          class="text-sm md:text-base leading-relaxed"
                          classList={{
                            "text-stone-700": message.from === "assistant",
                            "text-white": message.from === "user",
                          }}
                        >
                          {message.text}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>

          {/* Input Area - Fixed at bottom */}
          <div class="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-amber-50 via-amber-50/95 to-transparent pt-4 pb-6 px-6">
            <div class="max-w-4xl mx-auto">
              <Show
                when={showInput()}
                fallback={
                  <button
                    class="w-full px-6 py-4 bg-white border-2 border-stone-200 rounded-2xl shadow-sm hover:border-stone-400 transition-colors text-stone-500 text-left"
                    onClick={() => setShowInput(true)}
                  >
                    Type a message...
                  </button>
                }
              >
                <div class="flex items-start gap-3">
                  {/* User Avatar */}
                  <div class="flex-shrink-0 w-10 h-10 rounded-full bg-stone-300 flex items-center justify-center">
                    <span class="text-stone-600 text-sm font-semibold">
                      You
                    </span>
                  </div>

                  {/* Input Box */}
                  <div class="flex-1">
                    <div class="bg-white border-2 border-stone-200 rounded-2xl rounded-tl-sm shadow-sm focus-within:border-stone-400 transition-colors">
                      <textarea
                        class="w-full p-4 bg-transparent resize-none outline-none text-stone-700 placeholder-stone-400"
                        placeholder="Type your message..."
                        rows="3"
                        value={newMessage()}
                        onInput={(e) => setNewMessage(e.currentTarget.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Escape") {
                            setShowInput(false);
                            setNewMessage("");
                          }
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                      />
                      <div class="border-t border-stone-200 px-4 py-3 flex items-center justify-between">
                        <button
                          class="text-xs text-stone-500 hover:text-stone-700 transition-colors"
                          onClick={() => {
                            setShowInput(false);
                            setNewMessage("");
                          }}
                        >
                          Cancel
                        </button>
                        <button
                          class="px-4 py-1.5 bg-stone-700 hover:bg-stone-800 text-white text-sm rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          onClick={handleSendMessage}
                          disabled={!newMessage().trim()}
                        >
                          Send
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </Show>
            </div>
          </div>
        </div>
      </div>
    </Page>
  );
};

export default MePage;
