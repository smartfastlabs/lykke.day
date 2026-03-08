import {
  faBars,
} from "@fortawesome/free-solid-svg-icons";
import {
  Component,
  ParentProps,
  Show,
  createMemo,
  createSignal,
} from "solid-js";
import { useNavigate } from "@solidjs/router";
import Page from "@/components/shared/layout/Page";
import { Icon } from "@/components/shared/Icon";
import ActionGridModal from "@/components/shared/ActionGridModal";
import {
  TomorrowDataProvider,
  useTomorrowData,
} from "@/pages/me/tomorrow/useTomorrowData";
import {
  createMeMenuActions,
  ME_MENU_SUBTITLE,
  ME_MENU_TITLE,
} from "@/components/shared/meMenuActions";

const TomorrowPageLayoutInner: Component<ParentProps> = (props) => {
  const navigate = useNavigate();
  const { day, isDayLoading, refetchAll } = useTomorrowData();
  const [isMenuOpen, setIsMenuOpen] = createSignal(false);

  const date = createMemo(() => {
    const dayValue = day();
    if (!dayValue) return new Date();
    const [year, month, dayNum] = dayValue.date.split("-").map(Number);
    return new Date(year, month - 1, dayNum);
  });

  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date()),
  );

  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric" }).format(
      date(),
    ),
  );

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);

  const closeMenu = () => setIsMenuOpen(false);
  const openMenu = () => setIsMenuOpen(true);
  return (
    <Page variant="app" hideFooter>
      <div class="min-h-[100dvh] box-border relative overflow-hidden">
        <Show
          when={!isDayLoading() && day()}
          fallback={
            <div class="relative z-10 p-8 text-center text-stone-400">
              Loading...
            </div>
          }
        >
          <div class="relative z-10 max-w-4xl mx-auto px-6 py-6">
            <div class="mb-5 md:mb-7">
              <div class="relative flex items-start justify-between mb-4">
                <div class="min-w-0">
                  <div class="flex items-center gap-3 text-stone-600 mb-2">
                    <span class="font-semibold text-lg text-amber-600/80">
                      Tomorrow
                    </span>
                  </div>
                  <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                    {dateLabel()}
                  </p>
                </div>
              </div>
            </div>
            {props.children}
          </div>
        </Show>
      </div>

      <button
        type="button"
        onClick={openMenu}
        aria-label="Menu"
        title="Menu"
        class="fixed z-50 flex h-10 w-10 items-center justify-center rounded-full border border-amber-200 bg-white/95 text-amber-800 shadow-lg shadow-amber-900/10 transition hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 print:hidden"
        style={{
          top: "calc(env(safe-area-inset-top) + 1rem)",
          right: "calc(env(safe-area-inset-right) + 1rem)",
        }}
      >
        <Icon icon={faBars} class="h-5 w-5 fill-amber-700" />
      </button>

      <ActionGridModal
        isOpen={isMenuOpen()}
        title={ME_MENU_TITLE}
        subtitle={ME_MENU_SUBTITLE}
        onClose={closeMenu}
        actions={createMeMenuActions({
          close: closeMenu,
          navigate,
          onRefresh: refetchAll,
        })}
      />
    </Page>
  );
};

export const TomorrowPageLayout: Component<ParentProps> = (props) => {
  return (
    <TomorrowDataProvider>
      <TomorrowPageLayoutInner>{props.children}</TomorrowPageLayoutInner>
    </TomorrowDataProvider>
  );
};

export default TomorrowPageLayout;
