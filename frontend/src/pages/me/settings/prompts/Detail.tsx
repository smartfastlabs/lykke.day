import { useSearchParams } from "@solidjs/router";
import {
  Component,
  For,
  Show,
  createEffect,
  createResource,
  createSignal,
} from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { templateAPI } from "@/utils/api";
import type { TemplateDetail, TemplatePart, TemplatePreview } from "@/types/api";

const PART_LABELS: Record<TemplatePart, string> = {
  system: "System",
  context: "Context",
  ask: "Ask",
};

const PromptTemplateDetailPage: Component = () => {
  const [params] = useSearchParams();
  const templateUsecase = () => params.usecase ?? "";

  const detailSource = () => {
    const usecase = templateUsecase();
    return usecase ? usecase : undefined;
  };
  const [detail, { refetch: refetchDetail }] = createResource<
    TemplateDetail,
    string
  >(detailSource, templateAPI.getDetail);
  const [preview, { refetch: refetchPreview }] = createResource<
    TemplatePreview,
    string
  >(detailSource, templateAPI.preview);

  const [partContent, setPartContent] = createSignal<Record<string, string>>({});
  const [savingPart, setSavingPart] = createSignal<string | null>(null);
  const [error, setError] = createSignal<Record<string, string>>({});
  const isSaving = () => savingPart() !== null;

  createEffect(() => {
    const current = detail();
    if (!current) return;
    const next: Record<string, string> = {};
    current.parts.forEach((part) => {
      next[part.part] = part.override?.content ?? part.system_content;
    });
    setPartContent(next);
  });

  const updatePartContent = (part: string, value: string) => {
    setPartContent((previous) => ({ ...previous, [part]: value }));
  };

  const setPartError = (part: string, message: string) => {
    setError((previous) => ({ ...previous, [part]: message }));
  };

  const handleSave = async (part: TemplatePart) => {
    const current = detail();
    if (!current) return;
    const partDetail = current.parts.find((item) => item.part === part);
    if (!partDetail) return;
    setPartError(part, "");
    setSavingPart(part);
    try {
      if (partDetail.override) {
        await templateAPI.update({
          id: partDetail.override.id,
          content: partContent()[part] ?? "",
        });
      } else {
        await templateAPI.create({
          usecase: current.usecase,
          key: part,
          content: partContent()[part] ?? "",
        });
      }
      await refetchDetail();
      await refetchPreview();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to save template override";
      setPartError(part, message);
    } finally {
      setSavingPart(null);
    }
  };

  const handleDelete = async (part: TemplatePart) => {
    const current = detail();
    if (!current) return;
    const partDetail = current.parts.find((item) => item.part === part);
    if (!partDetail?.override) return;
    setPartError(part, "");
    setSavingPart(part);
    try {
      await templateAPI.delete(partDetail.override.id);
      await refetchDetail();
      await refetchPreview();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete override";
      setPartError(part, message);
    } finally {
      setSavingPart(null);
    }
  };

  return (
    <SettingsPage
      heading="Prompt Template"
      bottomLink={{ label: "Back to Templates", url: "/me/settings/prompts" }}
    >
      <Show
        when={templateUsecase()}
        fallback={
          <div class="text-center text-gray-500 py-8">
            No template selected.
          </div>
        }
      >
        <Show
          when={detail()}
          fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
        >
          {(current) => (
            <div class="space-y-8">
              <div class="space-y-2">
                <div class="text-sm text-gray-500">Template</div>
                <div class="text-sm font-medium text-gray-900">
                  {current().name}
                </div>
                <div class="text-xs text-gray-500">{current().usecase}</div>
              </div>

              <For each={current().parts}>
                {(part) => (
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <div class="text-sm font-semibold text-gray-800">
                        {PART_LABELS[part.part]}
                      </div>
                      <Show when={part.override}>
                        <button
                          type="button"
                          onClick={() => handleDelete(part.part)}
                          class="text-sm text-red-600 hover:text-red-700"
                          disabled={isSaving()}
                        >
                          Delete Override
                        </button>
                      </Show>
                    </div>
                    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div class="space-y-2">
                        <div class="text-xs font-semibold text-gray-500 uppercase">
                          System Default
                        </div>
                        <textarea
                          class="w-full min-h-[180px] p-3 border border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-700"
                          value={part.system_content}
                          readOnly
                        />
                      </div>
                      <div class="space-y-2">
                        <div class="text-xs font-semibold text-gray-500 uppercase">
                          Your Override
                        </div>
                        <textarea
                          class="w-full min-h-[180px] p-3 border border-gray-200 rounded-lg text-sm"
                          value={partContent()[part.part] ?? ""}
                          onInput={(event) =>
                            updatePartContent(part.part, event.currentTarget.value)
                          }
                        />
                      </div>
                    </div>
                    <div class="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => handleSave(part.part)}
                        disabled={isSaving()}
                        class="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800 disabled:opacity-60"
                      >
                        {savingPart() === part.part ? "Saving..." : "Save Override"}
                      </button>
                    </div>
                    <Show when={error()[part.part]}>
                      <div class="text-sm text-red-600">{error()[part.part]}</div>
                    </Show>
                  </div>
                )}
              </For>

              <div class="space-y-4">
                <div class="text-sm font-semibold text-gray-800">Preview</div>
                <Show
                  when={preview()}
                  fallback={
                    <div class="text-sm text-gray-500">Loading preview...</div>
                  }
                >
                  {(currentPreview) => (
                    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
                      <div class="space-y-2">
                        <div class="text-xs font-semibold text-gray-500 uppercase">
                          System Prompt
                        </div>
                        <textarea
                          class="w-full min-h-[200px] p-3 border border-gray-200 rounded-lg text-sm"
                          value={currentPreview().system_prompt}
                          readOnly
                        />
                      </div>
                      <div class="space-y-2">
                        <div class="text-xs font-semibold text-gray-500 uppercase">
                          Context Prompt
                        </div>
                        <textarea
                          class="w-full min-h-[200px] p-3 border border-gray-200 rounded-lg text-sm"
                          value={currentPreview().context_prompt}
                          readOnly
                        />
                      </div>
                      <div class="space-y-2">
                        <div class="text-xs font-semibold text-gray-500 uppercase">
                          Ask Prompt
                        </div>
                        <textarea
                          class="w-full min-h-[200px] p-3 border border-gray-200 rounded-lg text-sm"
                          value={currentPreview().ask_prompt}
                          readOnly
                        />
                      </div>
                      <div class="md:col-span-2 space-y-2">
                        <div class="text-xs font-semibold text-gray-500 uppercase">
                          Context Data
                        </div>
                        <pre class="w-full max-h-[280px] overflow-auto p-3 border border-gray-200 rounded-lg text-xs bg-gray-50">
                          {JSON.stringify(currentPreview().context_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </Show>
              </div>
            </div>
          )}
        </Show>
      </Show>
    </SettingsPage>
  );
};

export default PromptTemplateDetailPage;
