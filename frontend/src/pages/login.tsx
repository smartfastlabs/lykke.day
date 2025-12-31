import { createSignal } from "solid-js";
import Page from "../components/shared/layout/page";
import { authAPI } from "../utils/api";
import { Input, SubmitButton, FormError } from "../components/forms";

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
      window.location.href = "/";
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Authentication failed";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <Page>
      <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <h1 class="text-2xl font-medium text-neutral-900 text-center mb-8">
            Sign In
          </h1>

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

            <p class="text-sm text-center text-neutral-600">
              Don't have an account?{" "}
              <a
                href="/register"
                class="text-neutral-900 font-medium hover:underline"
              >
                Create one
              </a>
            </p>
          </form>
        </div>
      </div>
    </Page>
  );
}
