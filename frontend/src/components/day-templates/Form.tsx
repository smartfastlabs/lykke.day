import { Component, For, Show, createSignal } from "solid-js";
import { DayTemplate } from "@/types/api";
import { Input, SubmitButton, FormError, TextArea } from "@/components/forms";
import { Icon } from "@/components/shared/Icon";

interface FormProps {
  onSubmit: (template: Partial<DayTemplate>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: DayTemplate;
}

const DayTemplateForm: Component<FormProps> = (props) => {
  const normalizeTime = (value?: string | null) => {
    if (!value) return "";
    const parts = value.split(":");
    if (parts.length >= 2) {
      return `${parts[0].padStart(2, "0")}:${parts[1].padStart(2, "0")}`;
    }
    return value;
  };

  const [slug, setSlug] = createSignal(props.initialData?.slug ?? "");
  const [icon, setIcon] = createSignal(props.initialData?.icon ?? "");
  const [startTime, setStartTime] = createSignal(
    normalizeTime(props.initialData?.start_time)
  );
  const [endTime, setEndTime] = createSignal(
    normalizeTime(props.initialData?.end_time)
  );
  const [highLevelPlanTitle, setHighLevelPlanTitle] = createSignal(
    props.initialData?.high_level_plan?.title ?? ""
  );
  const [highLevelPlanText, setHighLevelPlanText] = createSignal(
    props.initialData?.high_level_plan?.text ?? ""
  );
  const [intentions, setIntentions] = createSignal<string[]>(
    props.initialData?.high_level_plan?.intentions ?? []
  );
  const [newIntention, setNewIntention] = createSignal("");

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    const title = highLevelPlanTitle().trim();
    const text = highLevelPlanText().trim();
    const startTimeValue = startTime().trim();
    const endTimeValue = endTime().trim();
    const template: Partial<DayTemplate> = {
      slug: slug().trim(),
      icon: icon().trim() || null,
      start_time: startTimeValue || null,
      end_time: endTimeValue || null,
      high_level_plan:
        title || text || intentions().length > 0
          ? {
              title: title || null,
              text: text || null,
              intentions: intentions(),
            }
          : null,
    };

    await props.onSubmit(template);
  };

  const isUpdate = !!props.initialData;

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <Input
        id="slug"
        placeholder="Slug"
        value={slug}
        onChange={setSlug}
        required
      />

      <Input
        id="icon"
        placeholder="Icon (Optional)"
        value={icon}
        onChange={setIcon}
      />

      <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-3">
        <div>
          <h2 class="text-lg font-medium text-neutral-900">Template Hours</h2>
          <p class="text-sm text-neutral-500">
            Set the default day start and end times.
          </p>
        </div>

        <Input
          id="start-time"
          type="time"
          placeholder="Start time (optional)"
          value={startTime}
          onChange={setStartTime}
        />

        <Input
          id="end-time"
          type="time"
          placeholder="End time (optional)"
          value={endTime}
          onChange={setEndTime}
        />
      </div>

      <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-3">
        <div>
          <h2 class="text-lg font-medium text-neutral-900">High Level Plan</h2>
          <p class="text-sm text-neutral-500">
            Keep a short plan for how you want the day to feel.
          </p>
        </div>

        <Input
          id="high-level-plan-title"
          placeholder="Plan title"
          value={highLevelPlanTitle}
          onChange={setHighLevelPlanTitle}
        />

        <TextArea
          id="high-level-plan-text"
          placeholder="Plan notes"
          value={highLevelPlanText}
          onChange={setHighLevelPlanText}
          rows={4}
        />

        <div class="space-y-2">
          <label class="block text-xs font-medium text-neutral-700">
            Intentions
          </label>
          <Show when={intentions().length > 0}>
            <ul class="space-y-1 mb-2">
              <For each={intentions()}>
                {(intention, index) => (
                  <li class="flex items-center gap-2 text-sm text-neutral-700 bg-neutral-50 rounded-lg px-3 py-2">
                    <span class="flex-1">{intention}</span>
                    <button
                      type="button"
                      onClick={() =>
                        setIntentions(intentions().filter((_, i) => i !== index()))
                      }
                      class="text-neutral-600 hover:text-neutral-700"
                      aria-label="Remove intention"
                    >
                      <Icon key="xMark" class="w-4 h-4" />
                    </button>
                  </li>
                )}
              </For>
            </ul>
          </Show>
          <div class="flex gap-2">
            <input
              type="text"
              class="flex-1 rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-200"
              placeholder="Add an intention..."
              value={newIntention()}
              onInput={(e) => setNewIntention(e.currentTarget.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  const trimmed = newIntention().trim();
                  if (trimmed) {
                    setIntentions([...intentions(), trimmed]);
                    setNewIntention("");
                  }
                }
              }}
            />
            <button
              type="button"
              onClick={() => {
                const trimmed = newIntention().trim();
                if (trimmed) {
                  setIntentions([...intentions(), trimmed]);
                  setNewIntention("");
                }
              }}
              disabled={!newIntention().trim()}
              class="px-3 py-2 rounded-lg bg-neutral-100 text-neutral-700 hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              aria-label="Add intention"
            >
              <Icon key="plus" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Day Template" : "Create Day Template"}
      />
    </form>
  );
};

export default DayTemplateForm;
