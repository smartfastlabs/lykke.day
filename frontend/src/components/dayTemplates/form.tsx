import { Component, createSignal } from "solid-js";
import { DayTemplate } from "../../types/api";

interface FormProps {
  onSubmit: (template: Partial<DayTemplate>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

const DayTemplateForm: Component<FormProps> = (props) => {
  const [slug, setSlug] = createSignal("");
  const [icon, setIcon] = createSignal("");

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    const template: Partial<DayTemplate> = {
      slug: slug().trim(),
      icon: icon().trim() || null,
    };

    await props.onSubmit(template);
  };

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <div>
        <label for="slug" class="sr-only">
          Slug
        </label>
        <input
          id="slug"
          type="text"
          placeholder="Slug"
          value={slug()}
          onInput={(e) => setSlug(e.currentTarget.value)}
          class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
          required
        />
      </div>

      <div>
        <label for="icon" class="sr-only">
          Icon (Optional)
        </label>
        <input
          id="icon"
          type="text"
          placeholder="Icon (Optional)"
          value={icon()}
          onInput={(e) => setIcon(e.currentTarget.value)}
          class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
        />
      </div>

      {props.error && (
        <p class="text-sm text-red-600 text-center">{props.error}</p>
      )}

      <button
        type="submit"
        disabled={props.isLoading}
        class="w-full py-3 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {props.isLoading ? "Creating..." : "Create Day Template"}
      </button>
    </form>
  );
};

export default DayTemplateForm;

