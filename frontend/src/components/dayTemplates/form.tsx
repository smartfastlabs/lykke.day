import { Component, createSignal } from "solid-js";
import { DayTemplate } from "@/types/api";
import { Input, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (template: Partial<DayTemplate>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: DayTemplate;
}

const DayTemplateForm: Component<FormProps> = (props) => {
  const [slug, setSlug] = createSignal(props.initialData?.slug ?? "");
  const [icon, setIcon] = createSignal(props.initialData?.icon ?? "");

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    const template: Partial<DayTemplate> = {
      slug: slug().trim(),
      icon: icon().trim() || null,
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
