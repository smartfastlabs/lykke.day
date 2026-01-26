import { Component, For, Show, createEffect, createSignal } from "solid-js";
import { DayTemplate } from "@/types/api";
import { Input, SubmitButton, FormError, TextArea } from "@/components/forms";
import { Icon } from "@/components/shared/Icon";

interface FormProps {
  onSubmit: (template: Partial<DayTemplate>) => Promise<void>;
  onChange?: (template: Partial<DayTemplate>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: DayTemplate;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
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

  const buildTemplate = (): Partial<DayTemplate> => {
    const title = highLevelPlanTitle().trim();
    const text = highLevelPlanText().trim();
    const startTimeValue = startTime().trim();
    const endTimeValue = endTime().trim();
    return {
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
  };

  createEffect(() => {
    props.onChange?.(buildTemplate());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildTemplate());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? (isUpdate ? "Update Day Template" : "Create Day Template");
  const loadingText = () => props.loadingText ?? (isUpdate ? "Updating..." : "Creating...");

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Basics</h2>
          <p class="text-sm text-stone-500">Name the template and choose an icon.</p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="day-template-slug">
              Slug
            </label>
            <Input
              id="day-template-slug"
              placeholder="Slug"
              value={slug}
              onChange={setSlug}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="day-template-icon">
              Icon
            </label>
            <Input
              id="day-template-icon"
              placeholder="Icon (optional)"
              value={icon}
              onChange={setIcon}
            />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Template Hours</h2>
          <p class="text-sm text-stone-500">
            Set the default day start and end times.
          </p>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="day-template-start">
              Start time
            </label>
            <Input
              id="day-template-start"
              type="time"
              placeholder="Start time"
              value={startTime}
              onChange={setStartTime}
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="day-template-end">
              End time
            </label>
            <Input
              id="day-template-end"
              type="time"
              placeholder="End time"
              value={endTime}
              onChange={setEndTime}
            />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">High Level Plan</h2>
          <p class="text-sm text-stone-500">
            Keep a short plan for how you want the day to feel.
          </p>
        </div>

        <div class="space-y-4">
          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="day-template-plan-title"
            >
              Plan title
            </label>
            <Input
              id="day-template-plan-title"
              placeholder="Plan title"
              value={highLevelPlanTitle}
              onChange={setHighLevelPlanTitle}
            />
          </div>

          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="day-template-plan-notes"
            >
              Plan notes
            </label>
            <TextArea
              id="day-template-plan-notes"
              placeholder="Plan notes"
              value={highLevelPlanText}
              onChange={setHighLevelPlanText}
              rows={4}
            />
          </div>

          <div class="space-y-2">
            <label class="block text-xs font-medium text-neutral-700">Intentions</label>
            <Show when={intentions().length > 0}>
              <ul class="space-y-1 mb-2">
                <For each={intentions()}>
                  {(intention, index) => (
                    <li class="flex items-center gap-2 text-sm text-neutral-700 bg-amber-50/50 rounded-lg px-3 py-2 border border-amber-100/70">
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
                class="flex-1 rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
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
                class="px-3 py-2 rounded-lg border border-amber-100/80 bg-amber-50/70 text-amber-700 hover:bg-amber-100 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                aria-label="Add intention"
              >
                <Icon key="plus" class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <FormError error={props.error} />

      {shouldShowSubmit() && (
        <SubmitButton
          isLoading={props.isLoading}
          loadingText={loadingText()}
          text={submitText()}
        />
      )}
    </form>
  );
};

export default DayTemplateForm;
