import { Component, For, Show } from "solid-js";
import type { CurrentUser } from "@/types/api/user";

const WEEKDAY_LABELS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

interface ProfilePreviewProps {
  user: CurrentUser;
}

const StatusPill: Component<{ label: string; active: boolean }> = (props) => (
  <span
    class="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
    classList={{
      "bg-green-100 text-green-800": props.active,
      "bg-neutral-100 text-neutral-600": !props.active,
    }}
  >
    {props.label}
  </span>
);

const ProfilePreview: Component<ProfilePreviewProps> = (props) => {
  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-3xl space-y-8">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Profile</h2>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <div class="text-sm font-medium text-neutral-500">Email</div>
              <div class="mt-1 text-base text-neutral-900">{props.user.email}</div>
            </div>
            <div>
              <div class="text-sm font-medium text-neutral-500">Phone number</div>
              <div class="mt-1 text-base text-neutral-900">
                <Show when={props.user.phone_number} fallback={<span class="text-neutral-500">Not set</span>}>
                  {props.user.phone_number}
                </Show>
              </div>
            </div>
            <div>
              <div class="text-sm font-medium text-neutral-500">Status</div>
              <div class="mt-1 text-base text-neutral-900">{props.user.status}</div>
            </div>
            <div>
              <div class="text-sm font-medium text-neutral-500">Updated</div>
              <div class="mt-1 text-base text-neutral-900">
                {props.user.updated_at ?? "Never"}
              </div>
            </div>
            <div>
              <div class="text-sm font-medium text-neutral-500">Timezone</div>
              <div class="mt-1 text-base text-neutral-900">
                <Show
                  when={props.user.settings.timezone}
                  fallback={<span class="text-neutral-500">Not set</span>}
                >
                  {props.user.settings.timezone}
                </Show>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Access flags</h2>
          <div class="flex flex-wrap gap-2">
            <StatusPill label="Active" active={props.user.is_active} />
            <StatusPill label="Superuser" active={props.user.is_superuser} />
            <StatusPill label="Verified" active={props.user.is_verified} />
          </div>
        </div>

        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Template defaults</h2>
          <p class="text-sm text-neutral-500">
            Default template slugs applied by weekday.
          </p>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <For each={WEEKDAY_LABELS}>
              {(label, index) => (
                <div class="rounded-md border border-neutral-200 px-3 py-2">
                  <div class="text-xs uppercase tracking-wide text-neutral-500">{label}</div>
                  <div class="text-sm text-neutral-900">
                    {props.user.settings.template_defaults[index()] ?? "default"}
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePreview;

