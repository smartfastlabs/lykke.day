import {
  Component,
  Show,
  createEffect,
  createMemo,
  createResource,
  createSignal,
} from "solid-js";

import SettingsPage from "@/components/shared/SettingsPage";
import AmendmentsEditor from "@/components/shared/AmendmentsEditor";
import { FormError, Select, SubmitButton } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { globalNotifications } from "@/providers/notifications";
import { authAPI, basePersonalityAPI, usecaseConfigAPI } from "@/utils/api";
import type { NotificationUseCaseConfig } from "@/types/api";
import type { LLMProvider } from "@/types/api/user";

const LLM_PROVIDERS: LLMProvider[] = ["anthropic", "openai"];

const LLMSettingsPage: Component = () => {
  const { user, refetch } = useAuth();
  const [basePersonalities] = createResource(basePersonalityAPI.list);
  const [notificationConfig, { refetch: refetchNotificationConfig }] =
    createResource<NotificationUseCaseConfig>(
      usecaseConfigAPI.getNotificationConfig
    );
  const [provider, setProvider] = createSignal<LLMProvider | "">("");
  const [basePersonalitySlug, setBasePersonalitySlug] = createSignal("default");
  const [llmPersonalityAmendments, setLlmPersonalityAmendments] = createSignal<
    string[]
  >([]);
  const [error, setError] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);

  createEffect(() => {
    const currentUser = user();
    if (currentUser) {
      setProvider(currentUser.settings.llm_provider ?? "");
      setBasePersonalitySlug(
        currentUser.settings.base_personality_slug ?? "default"
      );
      setLlmPersonalityAmendments(
        currentUser.settings.llm_personality_amendments ?? []
      );
    }
  });

  const basePersonalityOptions = createMemo(() => {
    const options =
      basePersonalities()?.map((option) => ({
        value: option.slug,
        label: option.label,
      })) ?? [];

    if (!options.some((option) => option.value === "default")) {
      options.unshift({ value: "default", label: "Default" });
    }

    return options;
  });

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    if (isSaving()) return;
    setError("");
    setIsSaving(true);
    const selectedProvider = provider();
    try {
      await authAPI.updateProfile({
        settings: {
          llm_provider: selectedProvider === "" ? null : selectedProvider,
          base_personality_slug: basePersonalitySlug().trim() || "default",
          llm_personality_amendments: llmPersonalityAmendments()
            .map((value) => value.trim())
            .filter(Boolean),
        },
      });
      await refetch();
      refetchNotificationConfig();
      globalNotifications.addSuccess("LLM settings updated");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update LLM settings";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SettingsPage
      heading="LLM"
      bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
    >
      <Show
        when={user()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <form onSubmit={handleSubmit} class="space-y-6 max-w-2xl">
          <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">
                Smart notifications
              </h2>
              <p class="text-sm text-neutral-500">
                Choose the LLM provider used to evaluate smart notifications.
              </p>
            </div>

            <div class="space-y-2">
              <label
                class="text-sm font-medium text-neutral-500"
                for="llm-provider"
              >
                Provider
              </label>
              <Select<LLMProvider | "">
                id="llm-provider"
                value={provider}
                onChange={setProvider}
                options={LLM_PROVIDERS}
                placeholder="No provider selected"
              />
              <p class="text-xs text-neutral-400">
                Leave this empty to disable LLM-based smart notifications.
              </p>
            </div>
          </div>

          <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">
                Base personality
              </h2>
              <p class="text-sm text-neutral-500">
                Set the default tone used across system prompts.
              </p>
            </div>

            <div class="space-y-2">
              <label
                class="text-sm font-medium text-neutral-500"
                for="base-personality"
              >
                Personality
              </label>
              <Select<string>
                id="base-personality"
                placeholder="Select a base personality"
                value={basePersonalitySlug}
                onChange={setBasePersonalitySlug}
                options={basePersonalityOptions()}
              />
            </div>

            <AmendmentsEditor
              heading="Personality amendments"
              description="Add instructions that should override your base personality."
              amendments={llmPersonalityAmendments()}
              onChange={setLlmPersonalityAmendments}
              placeholder="Add a personality tweak..."
              class="pt-4 border-t border-neutral-200"
              disabled={isSaving()}
            />
          </div>

          <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">
                Prompt preview
              </h2>
              <p class="text-sm text-neutral-500">
                Preview of the system prompt used for notification decisions.
                Save changes to refresh.
              </p>
            </div>

            <Show
              when={!notificationConfig.loading}
              fallback={<div class="text-sm text-neutral-500">Loading...</div>}
            >
              <Show
                when={notificationConfig()?.rendered_prompt}
                fallback={
                  <div class="text-sm text-neutral-500">
                    No prompt available yet.
                  </div>
                }
              >
                <div class="bg-gray-50 border border-gray-200 rounded-md p-4 overflow-auto">
                  <pre class="text-sm text-gray-800 whitespace-pre-wrap font-mono">
                    {notificationConfig()?.rendered_prompt}
                  </pre>
                </div>
              </Show>
            </Show>
          </div>

          <FormError error={error()} />

          <SubmitButton
            isLoading={isSaving()}
            loadingText="Saving..."
            text="Save settings"
          />
        </form>
      </Show>
    </SettingsPage>
  );
};

export default LLMSettingsPage;
