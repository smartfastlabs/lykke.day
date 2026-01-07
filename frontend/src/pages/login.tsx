import { createSignal } from "solid-js";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { authAPI } from "@/utils/api";

export default function Login() {
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (e: Event) => {
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
      window.location.href = "/me";
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

      <form onSubmit={handleSubmit} class="space-y-6">
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
          Don't have an account?{" "}
          <a
            href="/early-access"
            class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
          >
            Join the waitlist
          </a>
        </p>
      </form>
    </ModalPage>
  );
}
