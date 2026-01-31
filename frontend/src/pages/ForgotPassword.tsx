import { Show, createSignal } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { authAPI } from "@/utils/api";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [phoneNumber, setPhoneNumber] = createSignal("");
  const [code, setCode] = createSignal("");
  const [step, setStep] = createSignal<"phone" | "code">("phone");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleRequestCode = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!phoneNumber() || !phoneNumber().trim()) {
      setError("Phone number required");
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.requestSmsCode(phoneNumber().trim());
      setStep("code");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Unable to send login code";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!code() || !code().trim()) {
      setError("Verification code required");
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.verifySmsCode(phoneNumber().trim(), code().trim());
      navigate("/me/today");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Invalid or expired code";
      setError(message);
      setIsLoading(false);
    }
  };

  return (
    <ModalPage subtitle="We'll text you a code to sign in.">
      <div class="text-center space-y-1">
        <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
          sign in with SMS
        </p>
        <p class="text-lg font-semibold text-stone-800">
          {step() === "phone" ? "Enter your phone number" : "Enter the code"}
        </p>
      </div>

      <Show
        when={step() === "phone"}
        fallback={
          <form onSubmit={handleVerifyCode} class="space-y-6">
            <p class="text-sm text-stone-600">
              We sent a 6-digit code to {phoneNumber()}
            </p>

            <Input
              id="code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={setCode}
              autocomplete="one-time-code"
            />

            <FormError error={error()} />

            <SubmitButton
              isLoading={isLoading()}
              loadingText="Verifying..."
              text="Verify & sign in"
            />

            <p class="text-sm text-center text-stone-600">
              Wrong number?{" "}
              <button
                type="button"
                onClick={() => {
                  setStep("phone");
                  setCode("");
                  setError("");
                }}
                class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
              >
                Go back
              </button>
            </p>
          </form>
        }
      >
        <form onSubmit={handleRequestCode} class="space-y-6">
          <Input
            id="phone"
            type="tel"
            placeholder="Phone number (e.g. +1 555 123 4567)"
            value={phoneNumber}
            onChange={setPhoneNumber}
            autocomplete="tel"
            required
          />

          <FormError error={error()} />

          <SubmitButton
            isLoading={isLoading()}
            loadingText="Sending code..."
            text="Send login code"
          />

          <p class="text-sm text-center text-stone-600">
            Remember your password?{" "}
            <A
              href="/login"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Sign in
            </A>
          </p>
        </form>
      </Show>
    </ModalPage>
  );
}
