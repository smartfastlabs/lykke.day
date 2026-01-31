import { createSignal } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { authAPI } from "@/utils/api";

type Mode = "phone" | "email" | "code";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = createSignal<Mode>("phone");
  const [phoneNumber, setPhoneNumber] = createSignal("");
  const [code, setCode] = createSignal("");
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
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
      setMode("code");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Unable to send code";
      setError(errorMessage);
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
      const errorMessage =
        err instanceof Error ? err.message : "Invalid or expired code";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  const handleEmailLogin = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!email()) {
      setError("Email required");
      return;
    }

    if (!password()) {
      setError("Password required");
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.login(email(), password());
      navigate("/me/today");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Authentication failed";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <ModalPage subtitle="A soft landing to start your day with intention.">
      <div class="text-center space-y-1">
        <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
          welcome back
        </p>
        <p class="text-lg font-semibold text-stone-800">Sign in</p>
      </div>

      {mode() === "phone" && (
        <form onSubmit={handleRequestCode} class="space-y-6">
          <Input
            id="phone"
            type="tel"
            placeholder="Phone number (e.g. +1 555 123 4567)"
            value={phoneNumber}
            onChange={setPhoneNumber}
            autocomplete="tel"
          />

          <FormError error={error()} />

          <SubmitButton
            isLoading={isLoading()}
            loadingText="Sending code..."
            text="Send login code"
          />

          <p class="text-sm text-center text-stone-600">
            Prefer email?{" "}
            <button
              type="button"
              onClick={() => {
                setMode("email");
                setError("");
              }}
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Sign in with email
            </button>
          </p>

          <p class="text-sm text-center text-stone-600">
            Don't have an account?{" "}
            <A
              href="/early-access"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Join the waitlist
            </A>
          </p>
        </form>
      )}

      {mode() === "code" && (
        <form onSubmit={handleVerifyCode} class="space-y-6">
          <p class="text-sm text-stone-600">
            Enter the 6-digit code we sent to {phoneNumber()}
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
                setMode("phone");
                setCode("");
                setError("");
              }}
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Go back
            </button>
          </p>
        </form>
      )}

      {mode() === "email" && (
        <form onSubmit={handleEmailLogin} class="space-y-6">
          <Input
            id="email"
            type="email"
            placeholder="Email"
            value={email}
            onChange={setEmail}
            autocomplete="email"
          />

          <Input
            id="password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={setPassword}
            autocomplete="current-password"
          />

          <FormError error={error()} />

          <SubmitButton
            isLoading={isLoading()}
            loadingText="Signing in..."
            text="Continue"
          />

          <p class="text-sm text-center text-stone-600">
            <A
              href="/forgot-password"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Forgot your password?
            </A>
          </p>

          <p class="text-sm text-center text-stone-600">
            Prefer phone?{" "}
            <button
              type="button"
              onClick={() => {
                setMode("phone");
                setError("");
              }}
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Sign in with SMS
            </button>
          </p>

          <p class="text-sm text-center text-stone-600">
            Don't have an account?{" "}
            <A
              href="/early-access"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              Join the waitlist
            </A>
          </p>
        </form>
      )}
    </ModalPage>
  );
}
