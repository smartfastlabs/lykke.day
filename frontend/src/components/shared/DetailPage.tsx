import { Component, Show, JSX, createSignal } from "solid-js";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";

interface DetailPageProps {
  heading: string;
  bottomLink?: {
    label: string;
    url: string;
  };
  preview: JSX.Element;
  edit: JSX.Element;
  additionalActionButtons?: ActionButton[];
  onDelete?: () => void;
}

const DetailPage: Component<DetailPageProps> = (props) => {
  const [isEditMode, setIsEditMode] = createSignal(false);

  const actionButtons = (): ActionButton[] => {
    const buttons: ActionButton[] = [
      {
        label: isEditMode() ? "View Mode" : "Edit Mode",
        onClick: () => setIsEditMode((prev) => !prev),
      },
    ];

    if (props.onDelete) {
      buttons.push({
        label: "Delete",
        onClick: props.onDelete,
      });
    }

    if (props.additionalActionButtons) {
      buttons.push(...props.additionalActionButtons);
    }

    return buttons;
  };

  return (
    <SettingsPage
      heading={props.heading}
      actionButtons={actionButtons()}
      bottomLink={props.bottomLink}
    >
      <Show when={isEditMode()} fallback={props.preview}>
        {props.edit}
      </Show>
    </SettingsPage>
  );
};

export default DetailPage;

