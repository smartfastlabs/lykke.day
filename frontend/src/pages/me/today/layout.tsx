import Page from "@/components/shared/layout/Page";
import { Show, Component, ParentProps } from "solid-js";
import { useSheppard } from "@/providers/sheppard";

export const TodayPageLayout: Component<ParentProps> = (props) => {
  const { dayContext, isLoading } = useSheppard();

  return (
    <Page>
      <div class="min-h-screen relative overflow-hidden">
        {/* Background gradients */}
        <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

        {/* Decorative blurs */}
        <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
        <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

        <Show
          when={!isLoading() && dayContext()}
          fallback={
            <div class="relative z-10 p-8 text-center text-stone-400">
              Loading...
            </div>
          }
        >
          <div class="relative z-10 max-w-4xl mx-auto px-6 py-12 md:py-16">
            {props.children}
          </div>
        </Show>
      </div>
    </Page>
  );
};

export default TodayPageLayout;
