import {
  faBell,
  faBars,
  faBrain,
  faCalendarDay,
  faCompass,
  faEnvelope,
  faGear,
  faPenToSquare,
  faRotate,
} from "@fortawesome/free-solid-svg-icons";
import { Show, Component, ParentProps, createMemo, createSignal } from "solid-js";
import Page from "@/components/shared/layout/Page";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import TimeBlocksSummary from "@/components/today/TimeBlocksSummary";
import ActionGridModal from "@/components/shared/ActionGridModal";
import { useNavigate } from "@solidjs/router";

export const TodayPageLayout: Component<ParentProps> = (props) => {
  const navigate = useNavigate();
  const { day, sync } = useStreamingData();
  const [isMenuOpen, setIsMenuOpen] = createSignal(false);

  const date = createMemo(() => {
    const dayValue = day();
    if (!dayValue) return new Date();

    // Parse date string as local date to avoid timezone issues
    // e.g., "2026-01-15" should be Jan 15 in local time, not UTC midnight
    const [year, month, dayNum] = dayValue.date.split("-").map(Number);
    return new Date(year, month - 1, dayNum); // month is 0-indexed
  });

  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date()),
  );

  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(date()),
  );

  const planTitle = createMemo(() => {
    const title = day()?.high_level_plan?.title ?? "";
    return title.trim();
  });

  const isWorkday = createMemo(() => {
    const dayValue = day();
    return Boolean(dayValue?.tags?.includes("WORKDAY"));
  });

  const timeBlocks = createMemo(() => day()?.template?.time_blocks ?? []);
  const dayDate = createMemo(() => day()?.date);

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);

  const closeMenu = () => setIsMenuOpen(false);
  const openMenu = () => setIsMenuOpen(true);
  const menuNavigate = (url: string) => {
    closeMenu();
    navigate(url);
  };

  return (
    <Page variant="app" hideFooter>
      <div class="min-h-[100dvh] box-border relative overflow-hidden">
        <div class="relative z-10 max-w-4xl mx-auto px-6 py-6">
          <div class="mb-5 md:mb-7">
            <div class="relative flex items-start justify-between mb-4">
              <div class="min-w-0">
                <div class="flex items-center gap-3 text-stone-600 mb-2">
                  <span class="font-semibold text-lg text-amber-600/80 leading-snug break-words">
                    {planTitle() || dateLabel()}
                  </span>
                </div>
                <Show when={planTitle()}>
                  <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                    {dateLabel()}
                  </p>
                </Show>
                <Show when={isWorkday()}>
                  <span class="mt-3 inline-flex px-3 py-1.25 rounded-full bg-amber-50/95 text-amber-600 text-[11px] font-semibold uppercase tracking-wide border border-amber-100/80 shadow-sm shadow-amber-900/5">
                    Workday
                  </span>
                </Show>
              </div>
            </div>
            <TimeBlocksSummary timeBlocks={timeBlocks()} dayDate={dayDate()} />
          </div>
          {props.children}
        </div>
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
        title="Menu"
        subtitle="Quick actions for today"
        onClose={closeMenu}
        actions={[
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
            onClick: () => {
              closeMenu();
              sync();
            },
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
        ]}
      />
    </Page>
  );
};

export default TodayPageLayout;
