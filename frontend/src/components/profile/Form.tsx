import { Component, For, createEffect, createMemo, createResource, createSignal } from "solid-js";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { dayTemplateAPI } from "@/utils/api";
import type { DayTemplate } from "@/types/api";
import type {
  CurrentUser,
  UserProfileUpdate,
  UserStatus,
} from "@/types/api/user";

const WEEKDAY_LABELS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

interface ProfileFormProps {
  initialData: CurrentUser;
  onSubmit: (payload: UserProfileUpdate) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  onChange?: (payload: UserProfileUpdate) => void;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const ProfileForm: Component<ProfileFormProps> = (props) => {
  const [dayTemplates] = createResource<DayTemplate[]>(dayTemplateAPI.getAll);
  const [phoneNumber, setPhoneNumber] = createSignal(props.initialData.phone_number ?? "");
  const [status, setStatus] = createSignal<UserStatus>(props.initialData.status);
  const [isActive, setIsActive] = createSignal(props.initialData.is_active);
  const [isSuperuser, setIsSuperuser] = createSignal(props.initialData.is_superuser);
  const [isVerified, setIsVerified] = createSignal(props.initialData.is_verified);
  const [timezone, setTimezone] = createSignal(
    props.initialData.settings.timezone ?? ""
  );
  const [templateDefaults, setTemplateDefaults] = createSignal<string[]>(
    Array.from(
      { length: 7 },
      (_, idx) => props.initialData.settings.template_defaults[idx] ?? "default"
    )
  );

  const templateOptions = createMemo<string[]>(() => {
    const baseOptions = ["default"];
    const templateSlugs =
      dayTemplates()
        ?.map((template) => template.slug)
        .filter(Boolean) ?? [];
    const existingValues = templateDefaults().filter(Boolean);

    return Array.from(new Set([...baseOptions, ...templateSlugs, ...existingValues]));
  });

  const updateTemplateDefault = (index: number, value: string) => {
    setTemplateDefaults((prev) => {
      const updated = [...prev];
      updated[index] = value;
      return updated;
    });
  };

  const buildPayload = (): UserProfileUpdate => ({
    phone_number: phoneNumber().trim() || null,
    status: status(),
    is_active: isActive(),
    is_superuser: isSuperuser(),
    is_verified: isVerified(),
    settings: {
      template_defaults: templateDefaults().map((value) => value.trim() || "default"),
      timezone: timezone().trim() || null,
    },
  });

  createEffect(() => {
    props.onChange?.(buildPayload());
  });

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    await props.onSubmit(buildPayload());
  };

  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? "Update Profile";
  const loadingText = () => props.loadingText ?? "Updating...";

  return (
    <form id={props.formId} class="space-y-8" onSubmit={handleSubmit}>
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-6 shadow-sm space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-stone-800">Profile</h2>
            <p class="text-sm text-stone-500">Update your account information.</p>
          </div>
          <div class="text-xs text-stone-400">Email cannot be changed</div>
        </div>

        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600">Email</label>
            <div class="w-full rounded-lg border border-dashed border-amber-100/80 bg-amber-50/40 px-4 py-3 text-neutral-700">
              {props.initialData.email}
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="profile-phone">
              Phone number
            </label>
            <Input
              id="profile-phone"
              placeholder="Phone number"
              value={phoneNumber}
              onChange={setPhoneNumber}
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="profile-timezone">
              Timezone
            </label>
            <Input
              id="profile-timezone"
              placeholder="e.g. America/Chicago"
              value={timezone}
              onChange={setTimezone}
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="profile-status">
              Status
            </label>
            <Select<UserStatus>
              id="profile-status"
              value={status}
              onChange={setStatus}
              options={["active", "new-lead"]}
              placeholder="Status"
            />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold text-stone-800">Access flags</h2>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <label class="flex items-center gap-3 rounded-md border border-amber-100/80 px-3 py-2">
            <input
              type="checkbox"
              checked={isActive()}
              onChange={(event) => setIsActive(event.currentTarget.checked)}
              class="h-4 w-4 rounded border-neutral-300 text-stone-900 focus:ring-amber-300"
            />
            <span class="text-sm text-neutral-800">Active</span>
          </label>

          <label class="flex items-center gap-3 rounded-md border border-amber-100/80 px-3 py-2">
            <input
              type="checkbox"
              checked={isSuperuser()}
              onChange={(event) => setIsSuperuser(event.currentTarget.checked)}
              class="h-4 w-4 rounded border-neutral-300 text-stone-900 focus:ring-amber-300"
            />
            <span class="text-sm text-neutral-800">Superuser</span>
          </label>

          <label class="flex items-center gap-3 rounded-md border border-amber-100/80 px-3 py-2">
            <input
              type="checkbox"
              checked={isVerified()}
              onChange={(event) => setIsVerified(event.currentTarget.checked)}
              class="h-4 w-4 rounded border-neutral-300 text-stone-900 focus:ring-amber-300"
            />
            <span class="text-sm text-neutral-800">Verified</span>
          </label>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-6 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Template defaults</h2>
          <p class="text-sm text-stone-500">
            Pick which day template to apply by default for each weekday.
          </p>
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <For each={WEEKDAY_LABELS}>
            {(label, index) => (
              <div class="space-y-1">
                <label class="text-xs font-medium text-neutral-600">{label}</label>
                <Select<string>
                  id={`template-default-${index()}`}
                  placeholder={`${label} template`}
                  value={() => templateDefaults()[index()] || "default"}
                  onChange={(value) => updateTemplateDefault(index(), value)}
                  options={templateOptions()}
                />
              </div>
            )}
          </For>
        </div>
      </div>

      <FormError error={props.error} />

      {shouldShowSubmit() && (
        <SubmitButton
          isLoading={props.isLoading}
          loadingText={loadingText()}
          text={submitText()}
        />
      )}
    </form>
  );
};

export default ProfileForm;

