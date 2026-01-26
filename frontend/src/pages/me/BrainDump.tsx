import { Component, Show, createMemo, createSignal } from "solid-js";
import Page from "@/components/shared/layout/Page";
import { useStreamingData } from "@/providers/streamingData";
import BrainDumpList from "@/components/brain-dump/List";
import { Icon } from "@/components/shared/Icon";
import { faBrain } from "@fortawesome/free-solid-svg-icons";

const BrainDumpPage: Component = () => {
  const { brainDumps, addBrainDumpItem, isLoading } = useStreamingData();
  const [newItemText, setNewItemText] = createSignal("");
  const [isAdding, setIsAdding] = createSignal(false);

  const items = createMemo(() => brainDumps() ?? []);
  const hasItems = createMemo(() => items().length > 0);

  const handleAddItem = async () => {
    const text = newItemText().trim();
    if (!text || isAdding()) return;

    setIsAdding(true);
    try {
      await addBrainDumpItem(text);
      setNewItemText("");
    } catch (error) {
      console.error("Failed to add brain dump item:", error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleKeyPress = (e: globalThis.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAddItem();
    }
  };

  return (
    <Page variant="app" hideFooter>
      <div class="min-h-[100dvh] box-border relative overflow-hidden">
        <div class="relative z-10 max-w-3xl mx-auto px-6 py-8">
          <div class="flex items-center gap-3 mb-6">
            <Icon icon={faBrain} class="w-6 h-6 fill-sky-600" />
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-amber-600/80">
                Dump Mode
              </p>
              <h1 class="text-2xl font-semibold text-stone-800">Brain Dump</h1>
            </div>
          </div>

          <div class="bg-white/70 border border-white/70 shadow-lg shadow-sky-900/5 rounded-2xl p-6 backdrop-blur-sm">
            <div class="flex gap-2">
              <input
                type="text"
                value={newItemText()}
                onInput={(e) => setNewItemText(e.currentTarget.value)}
                onKeyPress={handleKeyPress}
                placeholder="Add a thought..."
                disabled={isAdding() || isLoading()}
                class="flex-1 px-3 py-2 text-sm bg-white/80 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-stone-400"
              />
              <button
                onClick={handleAddItem}
                disabled={!newItemText().trim() || isAdding() || isLoading()}
                class="w-9 h-9 flex items-center justify-center bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-sky-500"
                aria-label="Add brain dump item"
              >
                <Icon key="plus" class="w-4 h-4 fill-white" />
              </button>
            </div>

            <Show when={hasItems()}>
              <div class="mt-4 pt-4 border-t border-stone-200/50 space-y-0">
                <BrainDumpList items={items} />
              </div>
            </Show>
          </div>
        </div>
      </div>
    </Page>
  );
};

export default BrainDumpPage;
