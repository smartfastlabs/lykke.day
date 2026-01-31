import { Show, createSignal } from "solid-js";
import { A } from "@solidjs/router";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { marketingAPI } from "@/utils/api";

export default function EarlyAccess() {
  const [email, setEmail] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [success, setSuccess] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const value = email().trim();

    if (!value) {
      setError("Please enter an email address.");
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      await marketingAPI.requestEarlyAccess({ email: value });
      setSuccess(true);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Please enter a valid email address.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ModalPage subtitle="A soft landing to start your day with intention.">
      <Show
        when={!success()}
        fallback={
          <div class="space-y-6 text-center">
            <div class="space-y-2">
              <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                you're in
              </p>
              <p class="text-lg font-semibold text-stone-800">
                Thanks for joining
              </p>
            </div>
            <p class="text-stone-600 text-sm leading-relaxed">
              We&apos;ll reach out when lykke.day is ready. In the meantime,
              check out our{" "}
              <A
                href="/resources"
                class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
              >
                resources
              </A>
              .
            </p>
          </div>
        }
      >
        <div class="text-center space-y-1">
          <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
            early access
          </p>
          <p class="text-lg font-semibold text-stone-800">Join the waitlist</p>
        </div>

        <form onSubmit={handleSubmit} class="space-y-6">
          <Input
            id="email"
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(value) => {
              setEmail(value);
              setError("");
            }}
            autocomplete="email"
          />

          <FormError error={error()} />

          <SubmitButton
            isLoading={isLoading()}
            loadingText="Sending..."
            text="Request access"
          />

          <p class="text-stone-400 text-xs text-center">
            We only reach out about lykke.day. Unsubscribe anytime.
          </p>
          <p class="text-sm text-center text-stone-600">
            Prefer to sign in?{" "}
            <A
              href="/login"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Log in
            </A>
            .
          </p>
        </form>
      </Show>
    </ModalPage>
  );
}
