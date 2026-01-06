import { Component, Show, For, createSignal } from "solid-js";
import { FontAwesomeIcon } from "solid-fontawesome";
import {
  faBullseye,
  faRotateRight,
  faCalendar,
  faBell,
} from "@fortawesome/free-solid-svg-icons";
import Page from "@/components/shared/layout/page";

interface Feature {
  icon: any;
  title: string;
  description: string;
}

const Landing: Component = () => {
  const [contact, setContact] = createSignal("");
  const [showModal, setShowModal] = createSignal(false);
  const [submitted, setSubmitted] = createSignal(false);

  const handleOptIn = () => {
    if (contact().trim()) {
      setShowModal(false);
      setSubmitted(true);
    }
  };

  const features: Feature[] = [
    {
      icon: faBullseye,
      title: "One Day at a Time",
      description:
        "No backlogs. No guilt. Just small, meaningful goals for today.",
    },
    {
      icon: faRotateRight,
      title: "Gentle Routines",
      description:
        "Build rhythms that fit your life — not someone else's idea of productivity.",
    },
    {
      icon: faCalendar,
      title: "Calendar Aware",
      description:
        "We sync with your calendar so wellness fits into your real life — not around it.",
    },
    {
      icon: faBell,
      title: "Soft Reminders",
      description:
        "Nudges, not nagging. We'll help you remember what matters to you.",
    },
  ];

  return (
    <Page>
      <Show
        when={submitted()}
        fallback={
          <div class="min-h-screen bg-amber-50 flex flex-col items-center px-6 py-16">
            <div class="max-w-3xl w-full text-center">
              <h1 class="text-6xl md:text-7xl font-light text-stone-800 tracking-wide mb-10">
                lykke.day
              </h1>

              <div class="mb-16">
                <p class="text-6xl text-amber-300 font-serif leading-none">"</p>
                <p class="text-stone-700 text-xl italic leading-relaxed -mt-4 mb-2">
                  Lykke (n.) — the Danish art of finding happiness in everyday
                  moments.
                </p>
                <p class="text-stone-400 text-sm">pronounced: loo-kah</p>
              </div>

              <div class="grid sm:grid-cols-2 gap-5 mb-12">
                <For each={features}>
                  {(feature) => (
                    <div class="bg-white/60 backdrop-blur-sm rounded-2xl p-6 text-left">
                      <FontAwesomeIcon
                        icon={feature.icon as any}
                        class="w-7 h-7 text-amber-600 mb-3"
                      />
                      <h3 class="text-stone-800 font-medium mb-2">
                        {feature.title}
                      </h3>
                      <p class="text-stone-500 text-sm leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  )}
                </For>
              </div>

              <p class="text-stone-500 text-sm mb-6 max-w-sm mx-auto">
                A daily companion app — not another endless task list. Just
                small intentions, gentle check-ins, and space to breathe.
              </p>

              <button
                onClick={() => setShowModal(true)}
                class="px-8 py-3 bg-stone-800 text-amber-50 rounded-lg hover:bg-stone-700 transition-colors"
              >
                Get early access
              </button>
            </div>

            <Show when={showModal()}>
              <div class="fixed inset-0 bg-black/40 flex items-center justify-center px-6">
                <div class="bg-white rounded-xl p-8 max-w-sm w-full text-center shadow-xl">
                  <h2 class="text-xl text-stone-800 mb-4">Stay in the loop</h2>
                  <p class="text-stone-500 text-sm mb-5">
                    Leave your email or phone and we'll let you know when
                    lykke.day is ready.
                  </p>
                  <input
                    type="text"
                    value={contact()}
                    onInput={(e) => setContact(e.currentTarget.value)}
                    placeholder="Email or phone"
                    class="w-full px-4 py-3 mb-4 bg-stone-50 border border-stone-200 rounded-lg text-stone-700 placeholder-stone-400 focus:outline-none focus:border-stone-400 transition-colors"
                  />
                  <p class="text-stone-400 text-xs mb-5">
                    We'll only reach out about lykke.day. Unsubscribe anytime.
                  </p>
                  <div class="flex gap-3">
                    <button
                      onClick={() => setShowModal(false)}
                      class="flex-1 py-2 border border-stone-200 text-stone-600 rounded-lg hover:bg-stone-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleOptIn}
                      class="flex-1 py-2 bg-stone-800 text-white rounded-lg hover:bg-stone-700 transition-colors"
                    >
                      I'm in
                    </button>
                  </div>
                </div>
              </div>
            </Show>
          </div>
        }
      >
        <div class="min-h-screen bg-amber-50 flex flex-col items-center justify-center px-6">
          <div class="max-w-md text-center">
            <p class="text-stone-700 text-lg mb-8">We'll be in touch.</p>
            <p class="text-stone-500 italic">
              "Happiness is not something ready made. It comes from your own
              actions."
            </p>
            <p class="text-stone-400 text-sm mt-2">— Dalai Lama</p>
          </div>
        </div>
      </Show>
    </Page>
  );
};

export default Landing;

