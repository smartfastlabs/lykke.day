import { createSignal } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { Input, SubmitButton, FormError } from "@/components/forms";
import ModalPage from "@/components/shared/ModalPage";
import { authAPI } from "@/utils/api";

export default function Register() {
  const navigate = useNavigate();
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
      navigate("/me/today");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Registration failed";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <ModalPage subtitle="Create a calm space to set your daily intentions.">
      <div class="text-center space-y-1">
        <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
          join us
        </p>
        <p class="text-lg font-semibold text-stone-800">Create account</p>
      </div>

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

        <p class="text-sm text-center text-stone-600">
          Already have an account?{" "}
          <A
            href="/login"
            class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
          >
            Sign in
          </A>
        </p>
      </form>
    </ModalPage>
  );
}
