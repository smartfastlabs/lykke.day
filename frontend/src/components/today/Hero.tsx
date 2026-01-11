import { Component, Show, createSignal } from "solid-js";

export interface HeroProps {
  weekday: string;
  monthDay: string;
  isWorkday: boolean;
  userName?: string;
  greeting?: string;
  description?: string;
}

export const Hero: Component<HeroProps> = (props) => {
  const [isExpanded, setIsExpanded] = createSignal(false);
  const [showReplyBox, setShowReplyBox] = createSignal(false);

  return (
    <div class="relative mb-8 md:mb-12">
      {/* Assistant Message */}
      <div class="flex items-start gap-3 mb-3">
        {/* Avatar */}
        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-stone-700 to-stone-800 flex items-center justify-center shadow-md">
          <span class="text-white text-lg">✨</span>
        </div>

        {/* Message Container */}
        <div class="flex-1 max-w-3xl">
          {/* Name and timestamp */}
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-sm font-semibold text-stone-700">lykke</span>
            <span class="text-xs text-stone-400">
              {props.weekday}, {props.monthDay}
            </span>
            <Show when={props.isWorkday}>
              <span class="px-2 py-0.5 rounded-full bg-amber-400 text-amber-900 text-xs font-bold">
                Workday
              </span>
            </Show>
          </div>

          {/* Chat Bubble */}
          <div
            class="bg-stone-100 border border-stone-200 text-stone-800 rounded-2xl rounded-tl-sm shadow-sm cursor-pointer transition-all hover:shadow-md hover:bg-stone-50"
            onClick={() => setIsExpanded(!isExpanded())}
          >
            <div class="p-4">
              <Show when={props.description}>
                <p
                  class="text-stone-700 text-sm md:text-base leading-relaxed"
                  classList={{
                    "line-clamp-2": !isExpanded(),
                  }}
                >
                  {props.description}
                </p>
              </Show>

              <Show
                when={
                  !isExpanded() &&
                  props.description &&
                  props.description.length > 100
                }
              >
                <p class="text-stone-500 text-xs mt-2 italic">
                  Click to read more...
                </p>
              </Show>
            </div>

            {/* Expanded Actions */}
            <Show when={isExpanded()}>
              <div class="border-t border-stone-200 px-4 py-3 flex items-center gap-3">
                <button
                  class="text-xs text-stone-600 hover:text-stone-900 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowReplyBox(!showReplyBox());
                  }}
                >
                  💬 Reply
                </button>
                <button
                  class="text-xs text-stone-600 hover:text-stone-900 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsExpanded(false);
                  }}
                >
                  Show less
                </button>
              </div>
            </Show>
          </div>
        </div>
      </div>

      {/* Reply Box */}
      <Show when={showReplyBox()}>
        <div class="flex items-start gap-3">
          {/* User Avatar Placeholder */}
          <div class="flex-shrink-0 w-10 h-10 rounded-full bg-stone-300 flex items-center justify-center">
            <span class="text-stone-600 text-sm font-semibold">You</span>
          </div>

          {/* Reply Input */}
          <div class="flex-1 max-w-3xl">
            <div class="bg-white border-2 border-stone-200 rounded-2xl rounded-tl-sm shadow-sm focus-within:border-stone-400 transition-colors">
              <textarea
                class="w-full p-4 bg-transparent resize-none outline-none text-stone-700 placeholder-stone-400"
                placeholder="Type your message..."
                rows="3"
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setShowReplyBox(false);
                  }
                }}
              />
              <div class="border-t border-stone-200 px-4 py-3 flex items-center justify-between">
                <button
                  class="text-xs text-stone-500 hover:text-stone-700 transition-colors"
                  onClick={() => setShowReplyBox(false)}
                >
                  Cancel
                </button>
                <button
                  class="px-4 py-1.5 bg-stone-700 hover:bg-stone-800 text-white text-sm rounded-full transition-colors"
                  onClick={() => {
                    // TODO: Handle message send
                    setShowReplyBox(false);
                  }}
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </Show>
    </div>
  );
};
