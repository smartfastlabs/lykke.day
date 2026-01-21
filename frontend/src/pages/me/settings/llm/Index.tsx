import { Component, Show, createEffect, createSignal } from "solid-js";

import SettingsPage from "@/components/shared/SettingsPage";
import { FormError, Select, SubmitButton } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { globalNotifications } from "@/providers/notifications";
import { authAPI } from "@/utils/api";
import type { LLMProvider } from "@/types/api/user";

const LLM_PROVIDERS: LLMProvider[] = ["anthropic", "openai"];

const LLMSettingsPage: Component = () => {
  const { user, refetch } = useAuth();
  const [provider, setProvider] = createSignal<LLMProvider | "">("");
  const [error, setError] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);

  createEffect(() => {
    const currentUser = user();
    if (currentUser) {
      setProvider(currentUser.settings.llm_provider ?? "");
    }
  });

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    if (isSaving()) return;
    setError("");
    setIsSaving(true);
    try {
      await authAPI.updateProfile({
        settings: {
          llm_provider: provider() ? provider() : null,
        },
      });
      await refetch();
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
