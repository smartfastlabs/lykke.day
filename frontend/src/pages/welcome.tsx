import { useNavigate } from "@solidjs/router";
import { Component, For, Show, createResource, createSignal } from "solid-js";
import Page from "../components/shared/layout/page";
import { taskDefinitionAPI } from "../utils/api";
import { TaskDefinition } from "../types/api";
import { globalNotifications } from "../providers/notifications";

const Welcome: Component = () => {
  const navigate = useNavigate();
  const [availableTaskDefinitions] = createResource(
    taskDefinitionAPI.getAvailable
  );
  const [selectedIds, setSelectedIds] = createSignal<Set<string>>(new Set());
  const [isImporting, setIsImporting] = createSignal(false);
  const [searchTerm, setSearchTerm] = createSignal("");

  const toggleSelection = (name: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    const available = availableTaskDefinitions();
    if (!available) return;

    if (selectedIds().size === available.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(available.map((td) => td.name)));
    }
  };

  const handleImport = async () => {
    const available = availableTaskDefinitions();
    if (!available || selectedIds().size === 0) return;

    setIsImporting(true);
    try {
      const selected = available.filter((td) => selectedIds().has(td.name));
      // Remove user_id from available task definitions and let the backend assign it
      const toImport = selected.map((td) => ({
        name: td.name,
        description: td.description,
        type: td.type,
      })) as TaskDefinition[];

      await taskDefinitionAPI.bulkCreate(toImport);
      globalNotifications.addSuccess(
        `Successfully imported ${selected.length} task definition${selected.length > 1 ? "s" : ""}!`
      );
      navigate("/");
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to import task definitions";
      globalNotifications.addError(errorMessage);
    } finally {
      setIsImporting(false);
    }
  };

  const filteredTaskDefinitions = () => {
    const available = availableTaskDefinitions();
    if (!available) return [];
    const search = searchTerm().toLowerCase();
    if (!search) return available;
    return available.filter(
      (td) =>
        td.name.toLowerCase().includes(search) ||
        td.description.toLowerCase().includes(search) ||
        td.type.toLowerCase().includes(search)
    );
  };

  return (
    <Page>
      <div class="w-full px-5 py-4 max-w-2xl mx-auto">
        <div class="mb-8">
          <h1 class="text-3xl font-bold mb-2">Welcome to Planned.day!</h1>
          <p class="text-gray-600">
            Get started by importing some task definitions. You can always add
            more later.
          </p>
        </div>

        <Show
          when={availableTaskDefinitions()}
          fallback={
            <div class="text-center text-gray-500 py-8">
              Loading task definitions...
            </div>
          }
        >
          <div class="mb-6">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-4">
                <input
                  type="text"
                  placeholder="Search task definitions..."
                  value={searchTerm()}
                  onInput={(e) => setSearchTerm(e.currentTarget.value)}
                  class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
                />
                <button
                  onClick={toggleSelectAll}
                  class="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  {selectedIds().size === availableTaskDefinitions()!.length
                    ? "Deselect All"
                    : "Select All"}
                </button>
              </div>
              <div class="text-sm text-gray-600">
                {selectedIds().size} of {availableTaskDefinitions()!.length}{" "}
                selected
              </div>
            </div>
          </div>

          <div class="max-h-96 overflow-y-auto mb-6 border border-gray-200 rounded-lg">
            <For each={filteredTaskDefinitions()}>
              {(taskDef) => {
                const isSelected = () => selectedIds().has(taskDef.name);
                return (
                  <button
                    onClick={() => toggleSelection(taskDef.name)}
                    class={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                      isSelected() ? "bg-blue-50 border-blue-200" : ""
                    }`}
                  >
                    <div class="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={isSelected()}
                        class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        readOnly
                      />
                      <div class="flex-1 min-w-0">
                        <div class="font-medium text-gray-900">
                          {taskDef.name}
                        </div>
                        <div class="text-sm text-gray-500">
                          {taskDef.type}
                          {taskDef.description
                            ? ` • ${taskDef.description}`
                            : ""}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              }}
            </For>
          </div>

          <div class="flex gap-4">
            <button
              onClick={handleImport}
              disabled={selectedIds().size === 0 || isImporting()}
              class="flex-1 px-6 py-3 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isImporting()
                ? "Importing..."
                : `Import ${selectedIds().size} Task Definition${selectedIds().size !== 1 ? "s" : ""}`}
            </button>
            <button
              onClick={() => navigate("/")}
              class="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300 transition-colors"
            >
              Skip for Now
            </button>
          </div>
        </Show>
      </div>
    </Page>
  );
};

export default Welcome;
