import type { JSX } from "solid-js";
import Footer from "@/components/shared/layout/footer";

type ModalPageProps = {
  subtitle: string;
  title?: JSX.Element;
  children: JSX.Element;
};

export default function ModalPage({ subtitle, title, children }: ModalPageProps) {
  return (
    <div class="relative min-h-screen overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_45%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.08)_0%,_transparent_45%)]" />
      <div class="absolute top-24 right-12 w-56 h-56 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-28 left-8 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

      <div class="relative z-10 flex min-h-screen items-center justify-center px-6 py-12">
        <div class="w-full max-w-md space-y-8">
          <div class="text-center space-y-2">
            <h1 class="text-4xl font-bold tracking-tight text-stone-800">
              {title ?? (
                <>
                  lykke<span class="text-amber-500">.</span>day
                </>
              )}
            </h1>
            <p class="text-stone-500 text-sm md:text-base">{subtitle}</p>
          </div>

          <div class="bg-white/70 backdrop-blur-md border border-white/70 rounded-2xl shadow-xl shadow-amber-900/10 p-8 space-y-6">
            {children}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

