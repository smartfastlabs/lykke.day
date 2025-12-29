import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import Page from "../components/shared/layout/page";
import { authAPI } from "../utils/api";

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = createSignal("");
  const [email, setEmail] = createSignal("");
  const [phoneNumber, setPhoneNumber] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [confirmPassword, setConfirmPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!username() || !username().trim()) {
      setError("Username is required");
      return;
    }

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
      await authAPI.register(
        username().trim(),
        email().trim(),
        password(),
        phoneNumber().trim() || null
      );
      window.location.href = "/";
    } catch (err: any) {
      setError(err?.message || "Registration failed");
    } finally {
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
            <div>
              <label for="username" class="sr-only">
                Username
              </label>
              <input
                id="username"
                type="text"
                placeholder="Username"
                value={username()}
                onInput={(e) => setUsername(e.currentTarget.value)}
                class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
                autocomplete="username"
                required
              />
            </div>

            <div>
              <label for="email" class="sr-only">
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="Email"
                value={email()}
                onInput={(e) => setEmail(e.currentTarget.value)}
                class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
                autocomplete="email"
                required
              />
            </div>

            <div>
              <label for="phoneNumber" class="sr-only">
                Phone Number (Optional)
              </label>
              <input
                id="phoneNumber"
                type="tel"
                placeholder="Phone Number (Optional)"
                value={phoneNumber()}
                onInput={(e) => setPhoneNumber(e.currentTarget.value)}
                class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
                autocomplete="tel"
              />
            </div>

            <div>
              <label for="password" class="sr-only">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Password"
                value={password()}
                onInput={(e) => setPassword(e.currentTarget.value)}
                class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
                autocomplete="new-password"
                required
              />
            </div>

            <div>
              <label for="confirmPassword" class="sr-only">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword()}
                onInput={(e) => setConfirmPassword(e.currentTarget.value)}
                class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
                autocomplete="new-password"
                required
              />
            </div>

            {error() && (
              <p class="text-sm text-red-600 text-center">{error()}</p>
            )}

            <button
              type="submit"
              disabled={isLoading()}
              class="w-full py-3 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading() ? "Creating account..." : "Create Account"}
            </button>

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

