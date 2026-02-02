import { useNavigate } from "@solidjs/router";
import { Component, For } from "solid-js";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { faListCheck, faArrowsRotate } from "@fortawesome/free-solid-svg-icons";

import { Icon } from "@/components/shared/Icon";
import SettingsPage from "@/components/shared/SettingsPage";

interface NavItem {
  label: string;
  description: string;
  icon: IconDefinition;
  url: string;
}

interface NavSection {
  title: string;
  description: string;
  items: NavItem[];
}

const AdminIndexPage: Component = () => {
  const navigate = useNavigate();

  const navSections: NavSection[] = [
    {
      title: "Admin Tools",
      description: "System monitoring and debugging tools.",
      items: [
        {
          label: "Events",
          description: "View and search all domain events in the system.",
          icon: faListCheck,
          url: "/me/admin/events",
        },
        {
          label: "Sync Debugger",
          description: "Inspect streaming sync state and message log.",
          icon: faArrowsRotate,
          url: "/me/admin/sync",
        },
      ],
    },
  ];

  return (
    <SettingsPage heading="Admin">
      <div class="space-y-6">
        <div class="grid gap-6 lg:grid-cols-2">
          <For each={navSections}>
            {(section) => (
              <section class="rounded-3xl border border-amber-100/80 bg-white/80 p-6 shadow-sm shadow-amber-900/5">
                <div class="flex flex-col gap-2">
                  <h2 class="text-lg font-semibold text-stone-800">
                    {section.title}
                  </h2>
                  <p class="text-sm text-stone-500">{section.description}</p>
                </div>

                <div
                  class={`mt-5 grid gap-3 ${
                    section.items.length > 1 ? "sm:grid-cols-2" : ""
                  }`}
                >
                  <For each={section.items}>
                    {(item) => (
                      <button
                        onClick={() => navigate(item.url)}
                        class="group flex w-full items-start gap-3 rounded-2xl border border-amber-100/70 bg-amber-50/50 p-4 text-left transition hover:border-amber-200 hover:bg-white"
                      >
                        <div class="flex h-10 w-10 items-center justify-center rounded-xl border border-amber-100/80 bg-white/80 shadow-sm shadow-amber-900/5">
                          <Icon
                            icon={item.icon}
                            class="h-5 w-5 fill-amber-600/80 group-hover:fill-amber-700"
                          />
                        </div>
                        <div class="flex flex-1 flex-col gap-1">
                          <span class="text-sm font-semibold text-stone-700 group-hover:text-stone-800">
                            {item.label}
                          </span>
                          <span class="text-xs text-stone-500">
                            {item.description}
                          </span>
                        </div>
                      </button>
                    )}
                  </For>
                </div>
              </section>
            )}
          </For>
        </div>
      </div>
    </SettingsPage>
  );
};

export default AdminIndexPage;
