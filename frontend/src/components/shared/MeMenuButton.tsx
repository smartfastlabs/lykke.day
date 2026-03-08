import { Component, Show, createMemo, createSignal } from "solid-js";
import { useLocation, useNavigate } from "@solidjs/router";
import { faBars } from "@fortawesome/free-solid-svg-icons";

import { Icon } from "@/components/shared/Icon";
import ActionGridModal from "@/components/shared/ActionGridModal";
import {
  createMeMenuActions,
  ME_MENU_SUBTITLE,
  ME_MENU_TITLE,
} from "@/components/shared/meMenuActions";

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
        title={ME_MENU_TITLE}
        subtitle={ME_MENU_SUBTITLE}
        onClose={close}
        actions={createMeMenuActions({
          close,
          navigate,
        })}
      />
    </Show>
  );
};

export default MeMenuButton;

