import { Component, Show, createMemo, createSignal } from "solid-js";
import { useLocation, useNavigate } from "@solidjs/router";
import {
  faBars,
  faCalendarDay,
  faCompass,
  faGear,
  faHouse,
} from "@fortawesome/free-solid-svg-icons";

import { Icon } from "@/components/shared/Icon";
import ActionGridModal from "@/components/shared/ActionGridModal";

const MeMenuButton: Component = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = createSignal(false);

  const close = () => setIsOpen(false);
  const open = () => setIsOpen(true);

  const shouldShow = createMemo(() => {
    const path = location.pathname;
    const isMeRoute = path.startsWith("/me");
    const hasHeaderMenu =
      path.startsWith("/me/today") || path.startsWith("/me/tomorrow");
    return isMeRoute && !hasHeaderMenu;
  });

  const go = (url: string) => {
    close();
    navigate(url);
  };

  return (
    <Show when={shouldShow()}>
      <button
        onClick={open}
        class="fixed z-50 flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white/95 text-stone-800 shadow-lg shadow-stone-900/10 transition hover:bg-white active:scale-95 print:hidden"
        style={{
          top: "calc(env(safe-area-inset-top) + 1rem)",
          right: "calc(env(safe-area-inset-right) + 1rem)",
        }}
        aria-label="Menu"
        title="Menu"
      >
        <Icon icon={faBars} class="h-5 w-5 fill-current" />
      </button>

      <ActionGridModal
        isOpen={isOpen()}
        title="Menu"
        subtitle="Navigate and settings"
        onClose={close}
        actions={[
          { label: "Home", icon: faHouse, onClick: () => go("/me/today") },
          {
            label: "Tomorrow",
            icon: faCalendarDay,
            onClick: () => go("/me/tomorrow"),
          },
          { label: "Navigation", icon: faCompass, onClick: () => go("/me/nav") },
          { label: "Settings", icon: faGear, onClick: () => go("/me/settings") },
        ]}
      />
    </Show>
  );
};

export default MeMenuButton;

