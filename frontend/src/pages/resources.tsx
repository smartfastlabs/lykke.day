import { Component, createSignal, onMount } from "solid-js";
import { A } from "@solidjs/router";
import Footer from "@/components/shared/layout/Footer";
import { useAuth } from "@/providers/auth";
import { isBackForwardNavigation } from "@/utils/navigation";

interface ResourceBlock {
  title: string;
  description: string;
  href: string;
  gradient: string;
}

const Resources: Component = () => {
  const { isAuthenticated } = useAuth();
  const [mounted, setMounted] = createSignal(false);

  onMount(() => {
    // Skip animations if navigating via back/forward buttons
    if (isBackForwardNavigation()) {
      setMounted(true);
    } else {
      setTimeout(() => setMounted(true), 50);
    }
  });

  const AccountLink: Component = () => (
    <a
      href={isAuthenticated() ? "/me" : "/login"}
      class="absolute top-6 right-6 z-20 px-4 py-2 rounded-full bg-white/80 border border-stone-200 text-sm font-medium text-stone-700 shadow-sm hover:bg-white transition-colors"
    >
      {isAuthenticated() ? "My LYKKE" : "Log in"}
    </a>
  );

  const resources: ResourceBlock[] = [
    {
      title: "YouTube",
      description:
        "Channels that explore attention, rest, purpose, and kinder systems—voices that helped me rethink productivity and presence.",
      href: "/youtube",
      gradient: "from-red-500/80 to-red-600/80",
    },
    {
      title: "Podcasts",
      description:
        "Conversations on attention, burnout recovery, and building a kinder relationship with productivity.",
      href: "/podcasts",
      gradient: "from-purple-500/80 to-indigo-600/80",
    },
    {
      title: "Books",
      description:
        "Reflections, routines, and kinder ways to rebuild—books I leaned on while recovering from burnout.",
      href: "/books",
      gradient: "from-amber-600/80 to-orange-600/80",
    },
  ];

  return (
    <div class="min-h-screen relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

      <AccountLink />

      <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />
      <div class="absolute top-1/2 left-1/3 w-32 h-32 bg-gradient-to-r from-yellow-200/20 to-orange-200/20 rounded-full blur-2xl" />

      <div class="relative z-10 flex flex-col items-center px-6 py-20 md:py-28">
        <div class="max-w-3xl w-full text-center">
          <div
            class="mb-16 transition-all duration-1000 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(-20px)",
            }}
          >
            <h1 class="text-4xl md:text-4xl lg:text-8xl font-bold tracking-tight text-stone-800 mb-4">
              lykke
              <span class="text-amber-500">.</span>
              day
            </h1>
          </div>

          <div
            class="max-w-xl mx-auto mb-16 transition-all duration-1000 delay-300 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(20px)",
            }}
          >
            <div class="relative py-8">
              <div class="absolute left-0 top-0 w-8 h-8 border-l-2 border-t-2 border-amber-300/50" />
              <div class="absolute right-0 bottom-0 w-8 h-8 border-r-2 border-b-2 border-amber-300/50" />
              <p
                class="text-stone-600 text-lg md:text-xl italic leading-relaxed px-6"
                style={{
                  "font-family": "'Cormorant Garamond', Georgia, serif",
                }}
              >
                "True wisdom isn't found in the destination—it's gathered in the
                quiet practice of showing up, day after day."
              </p>
            </div>
          </div>

          <div class="grid sm:grid-cols-3 gap-6 mt-16">
            {resources.map((resource, index) => (
              <a
                href={resource.href}
                class="group relative overflow-hidden bg-white/50 backdrop-blur-sm border border-white/60 rounded-2xl p-8 text-center hover:bg-white/70 hover:shadow-xl hover:shadow-amber-900/10 transition-all duration-300 cursor-pointer"
                style={{
                  opacity: mounted() ? 1 : 0,
                  transform: mounted() ? "translateY(0)" : "translateY(30px)",
                  transition: `all 0.8s ease-out ${0.4 + index * 0.15}s`,
                }}
              >
                <div class="relative z-10">
                  <div
                    class={`mx-auto mb-6 w-16 h-16 rounded-2xl bg-gradient-to-br ${resource.gradient} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}
                  >
                    <div class="w-8 h-8 bg-white/90 rounded-lg" />
                  </div>
                  <h3 class="text-stone-800 font-bold text-xl mb-3">
                    {resource.title}
                  </h3>
                  <p class="text-stone-600 text-sm leading-relaxed">
                    {resource.description}
                  </p>
                </div>
                <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div class="absolute inset-0 bg-gradient-to-br from-amber-100/20 to-orange-100/20" />
                </div>
              </a>
            ))}
          </div>

          <div
            class="mt-16 transition-all duration-1000 delay-700 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(20px)",
            }}
          >
            <div class="bg-gradient-to-br from-stone-800 to-stone-700 rounded-2xl p-7 md:p-8 text-amber-50 shadow-lg shadow-stone-900/15 border border-white/10">
              <div class="space-y-4 text-center max-w-2xl mx-auto">
                <p class="text-xl md:text-2xl font-semibold leading-snug">
                  Or... just want an app to "fix" that one thing? 👀
                </p>
                <p class="text-amber-50/80 text-sm md:text-base leading-relaxed">
                  Look, we built this whole guide to help you understand the
                  journey. But if you're dead-set on finding an app to download
                  and call it progress... fine. We've got a list.
                </p>
                <A
                  href="/apps"
                  class="group relative inline-flex items-center justify-center px-8 py-3 bg-amber-100 text-stone-900 rounded-xl font-medium tracking-wide hover:bg-amber-200 transition-all duration-300 shadow-md shadow-stone-900/20 hover:-translate-y-0.5"
                >
                  <span class="relative z-10">Fine, show me the apps</span>
                  <div class="absolute inset-0 rounded-xl bg-amber-400/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </A>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="relative z-10">
        <Footer />
      </div>
    </div>
  );
};

export default Resources;
