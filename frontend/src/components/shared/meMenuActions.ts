import {
  faBell,
  faBrain,
  faCalendarDay,
  faCompass,
  faEnvelope,
  faGear,
  faPenToSquare,
  faRotate,
} from "@fortawesome/free-solid-svg-icons";
import type { ActionGridModalAction } from "@/components/shared/ActionGridModal";

type CreateMeMenuActionsOptions = {
  close: () => void;
  navigate: (url: string) => void;
  onRefresh?: () => void | Promise<void>;
};

export const ME_MENU_TITLE = "Menu";
export const ME_MENU_SUBTITLE = "Quick actions for today";

export const createMeMenuActions = (
  options: CreateMeMenuActionsOptions,
): ActionGridModalAction[] => {
  const menuNavigate = (url: string) => {
    options.close();
    options.navigate(url);
  };

  const refresh = () => {
    options.close();

    if (options.onRefresh) {
      return options.onRefresh();
    }

    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  return [
    {
      label: "Brain dumps",
      icon: faBrain,
      onClick: () => menuNavigate("/me/today/brain-dumps"),
    },
    {
      label: "Notifications",
      icon: faBell,
      onClick: () => menuNavigate("/me/today/notifications"),
    },
    {
      label: "Messages",
      icon: faEnvelope,
      onClick: () => menuNavigate("/me/today/messages"),
    },
    {
      label: "Tomorrow",
      icon: faCalendarDay,
      onClick: () => menuNavigate("/me/tomorrow"),
    },
    {
      label: "Events",
      icon: faCalendarDay,
      onClick: () => menuNavigate("/me/today/events"),
    },
    {
      label: "Edit day",
      icon: faPenToSquare,
      onClick: () => menuNavigate("/me/today/edit"),
    },
    {
      label: "Refresh",
      icon: faRotate,
      onClick: refresh,
    },
    {
      label: "Navigation",
      icon: faCompass,
      onClick: () => menuNavigate("/me/nav"),
    },
    {
      label: "Settings",
      icon: faGear,
      onClick: () => menuNavigate("/me/settings"),
    },
  ];
};
