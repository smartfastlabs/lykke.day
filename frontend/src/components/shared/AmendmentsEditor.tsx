import { Component, For, Show, createSignal } from "solid-js";

interface AmendmentsEditorProps {
  amendments: string[];
  onChange: (next: string[]) => void;
  heading?: string;
  description?: string;
  addLabel?: string;
  placeholder?: string;
  disabled?: boolean;
  class?: string;
}

const AmendmentsEditor: Component<AmendmentsEditorProps> = (props) => {
  const [newAmendment, setNewAmendment] = createSignal("");

  const handleAdd = () => {
    if (props.disabled) return;
    const text = newAmendment().trim();
    if (!text) return;
    props.onChange([...props.amendments, text]);
    setNewAmendment("");
  };

  const handleRemove = (index: number) => {
    if (props.disabled) return;
    props.onChange(props.amendments.filter((_, i) => i !== index));
  };

  const handleUpdate = (index: number, value: string) => {
    if (props.disabled) return;
    const updated = [...props.amendments];
    updated[index] = value;
    props.onChange(updated);
  };

  return (
    <div class={props.class ?? "space-y-3"}>
      <Show when={props.heading}>
        <h2 class="text-lg font-semibold mb-2">{props.heading}</h2>
      </Show>
      <Show when={props.description}>
        <p class="text-sm text-gray-600 mb-4">{props.description}</p>
      </Show>

      <div class="space-y-3">
        <For each={props.amendments}>
          {(amendment, index) => (
            <div class="flex gap-2 items-start">
              <textarea
                value={amendment}
                onInput={(e) => handleUpdate(index(), e.currentTarget.value)}
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                disabled={props.disabled}
              />
              <button
                type="button"
                onClick={() => handleRemove(index())}
                class="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                disabled={props.disabled}
              >
                Remove
              </button>
            </div>
          )}
        </For>

        <div class="flex gap-2">
          <textarea
            value={newAmendment()}
            onInput={(e) => setNewAmendment(e.currentTarget.value)}
            placeholder={props.placeholder ?? "Enter a new amendment..."}
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={props.disabled}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleAdd();
              }
            }}
          />
          <button
            type="button"
            onClick={handleAdd}
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            disabled={props.disabled}
          >
            {props.addLabel ?? "Add"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AmendmentsEditor;
