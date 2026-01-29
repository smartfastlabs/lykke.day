import { useNavigate } from "@solidjs/router";
import { Component, For } from "solid-js";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faFileLines,
  faRepeat,
  faUser,
  faCalendar,
  faListCheck,
  faCalendarDays,
  faBell,
  faClock,
  faBrain,
  faLightbulb,
  faBolt,
  faBullseye,
  faMobileScreenButton,
  faVolumeHigh,
} from "@fortawesome/free-solid-svg-icons";

import { Icon } from "@/components/shared/Icon";
import SettingsPage from "@/components/shared/SettingsPage";

interface SettingsLink {
  label: string;
  description: string;
  icon: IconDefinition;
  url: string;
}

interface SettingsSection {
  title: string;
  description: string;
  items: SettingsLink[];
}

const settingsSections: SettingsSection[] = [
  {
    title: "Routine Configuration",
    description: "Build the structure and defaults for your days.",
    items: [
      {
        label: "Day Templates",
        description: "Create reusable blueprints for a day.",
        icon: faFileLines,
        url: "/me/settings/day-templates",
      },
      {
        label: "Task Definitions",
        description: "Define the tasks you reuse the most.",
        icon: faListCheck,
        url: "/me/settings/task-definitions",
      },
      {
        label: "Routine Definitions",
        description: "Assemble steps into reusable routines.",
        icon: faRepeat,
        url: "/me/settings/routine-definitions",
      },
      {
        label: "Time Blocks",
        description: "Plan recurring blocks of time.",
        icon: faClock,
        url: "/me/settings/time-blocks",
      },
      {
        label: "Recurring Events",
        description: "Maintain repeating events and schedules.",
        icon: faCalendarDays,
        url: "/me/settings/recurring-events",
      },
    ],
  },
  {
    title: "User Configuration",
    description: "Personalize how you show up in the app.",
    items: [
      {
        label: "Profile",
        description: "Update your core profile details.",
        icon: faUser,
        url: "/me/settings/profile",
      },
      {
        label: "Factoids",
        description: "Capture personal truths and context.",
        icon: faLightbulb,
        url: "/me/settings/factoids",
      },
      {
        label: "Tactics",
        description: "Define the tactics you rely on.",
        icon: faBullseye,
        url: "/me/settings/tactics",
      },
      {
        label: "Triggers",
        description: "Track triggers that affect your flow.",
        icon: faBolt,
        url: "/me/settings/triggers",
      },
    ],
  },
  {
    title: "App Configuration",
    description: "Tune how the app behaves and responds.",
    items: [
      {
        label: "Notifications",
        description: "Manage reminders and alerts.",
        icon: faBell,
        url: "/me/settings/notifications",
      },
      {
        label: "Alarm Presets",
        description: "Save reusable alarm configurations.",
        icon: faBell,
        url: "/me/settings/alarms",
      },
      {
        label: "Push Subscriptions",
        description: "Manage device push permissions.",
        icon: faMobileScreenButton,
        url: "/me/settings/push-subscriptions",
      },
      {
        label: "Voice",
        description: "Pick the voice used by the kiosk.",
        icon: faVolumeHigh,
        url: "/me/settings/voice",
      },
      {
        label: "LLM",
        description: "Control AI behavior and integrations.",
        icon: faBrain,
        url: "/me/settings/llm",
      },
    ],
  },
  {
    title: "Integrations",
    description: "Connect external services to your day.",
    items: [
      {
        label: "Calendars",
        description: "Sync and manage calendar sources.",
        icon: faCalendar,
        url: "/me/settings/calendars",
      },
    ],
  },
];

const SettingsIndexPage: Component = () => {
  const navigate = useNavigate();

  return (
    <SettingsPage heading="Settings">
      <div class="space-y-6">
        <div class="grid gap-6 lg:grid-cols-2">
          <For each={settingsSections}>
            {(section) => (
              <section class="rounded-3xl border border-amber-100/80 bg-white/80 p-6 shadow-sm shadow-amber-900/5">
                <div class="flex flex-col gap-2">
                  <h2 class="text-lg font-semibold text-stone-800">
                    {section.title}
                  </h2>
                  <p class="text-sm text-stone-500">{section.description}</p>
                </div>

                <div class="mt-5 grid gap-3 sm:grid-cols-2">
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

export default SettingsIndexPage;
