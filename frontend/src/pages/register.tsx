import { createSignal } from "solid-js";
import Page from "@/components/shared/layout/page";
import { authAPI } from "@/utils/api";
import { Input, SubmitButton, FormError } from "@/components/forms";

export default function Register() {
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [confirmPassword, setConfirmPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!email() || !email().trim()) {
      setError("Email is required");
      return;
    }

    if (!password()) {
      setError("Password is required");
      return;
    }

    if (password() !== confirmPassword()) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.register(email().trim(), password());
      await authAPI.login(email().trim(), password());
      window.location.href = "/welcome";
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Registration failed";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <Page>
      <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <h1 class="text-2xl font-medium text-neutral-900 text-center mb-8">
            Create Account
          </h1>

          <form onSubmit={handleSubmit} class="space-y-6">
            <Input
              id="email"
              type="email"
              placeholder="Email"
              value={email}
              onChange={setEmail}
              autocomplete="email"
              required
            />

            <Input
              id="password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={setPassword}
              autocomplete="new-password"
              required
            />

            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={setConfirmPassword}
              autocomplete="new-password"
              required
            />

            <FormError error={error()} />

            <SubmitButton
              isLoading={isLoading()}
              loadingText="Creating account..."
              text="Create Account"
            />

            <p class="text-sm text-center text-neutral-600">
              Already have an account?{" "}
              <a
                href="/login"
                class="text-neutral-900 font-medium hover:underline"
              >
                Sign in
              </a>
            </p>
          </form>
        </div>
      </div>
    </Page>
  );
}
