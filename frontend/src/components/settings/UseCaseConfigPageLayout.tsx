import { Component, JSX, Show } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import AmendmentsEditor from "@/components/shared/AmendmentsEditor";
import LLMSnapshotDetails from "@/components/llm/LLMSnapshotDetails";
import type { LLMRunResultSnapshot } from "@/types/api";

interface UseCaseConfigPageLayoutProps {
  heading: string;
  error: string;
  isLoading: boolean;
  isSaving: boolean;
  amendments: string[];
  onAmendmentsChange: (next: string[]) => void;
  onSave: () => void;
  snapshotPreview: LLMRunResultSnapshot | null | undefined;
  snapshotLoading: boolean;
  saveButtonLabel?: string;
  amendmentsHeading?: string;
  amendmentsDescription: string;
  amendmentsPlaceholder?: string;
  children?: JSX.Element;
}

const UseCaseConfigPageLayout: Component<UseCaseConfigPageLayoutProps> = (
  props,
) => {
  return (
    <SettingsPage
      heading={props.heading}
      bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
    >
      <div class="space-y-6">
        <Show when={props.error}>
          <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {props.error}
          </div>
        </Show>

        <Show when={props.isLoading}>
          <div class="text-center text-gray-500 py-8">Loading...</div>
        </Show>

        {props.children}

        <AmendmentsEditor
          heading={props.amendmentsHeading ?? "User Customizations"}
          description={props.amendmentsDescription}
          amendments={props.amendments}
          onChange={props.onAmendmentsChange}
          placeholder={
            props.amendmentsPlaceholder ??
            "Enter a new customization instruction..."
          }
          disabled={props.isSaving || props.isLoading}
        />

        <div class="rounded-2xl border border-emerald-100/80 bg-white/80 p-5 shadow-sm shadow-emerald-900/5 space-y-4">
          <div>
            <h2 class="text-lg font-semibold mb-2">LLM Request Payload</h2>
            <p class="text-sm text-gray-600">
              Preview the exact payload that would be sent to the LLM provider.
            </p>
          </div>
          <Show
            when={!props.snapshotLoading}
            fallback={<div class="text-sm text-stone-500">Loading preview...</div>}
          >
            <Show
              when={props.snapshotPreview}
              fallback={
                <div class="text-sm text-stone-500">
                  No LLM snapshot preview is available yet. Save this use case
                  once and ensure an LLM provider is configured to preview the
                  request payload.
                </div>
              }
            >
              {(snapshot) => <LLMSnapshotDetails snapshot={snapshot()!} />}
            </Show>
          </Show>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={() => props.onSave()}
            disabled={props.isSaving || props.isLoading}
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {props.isSaving
              ? "Saving..."
              : (props.saveButtonLabel ?? "Save Changes")}
          </button>
        </div>
      </div>
    </SettingsPage>
  );
};

export default UseCaseConfigPageLayout;
