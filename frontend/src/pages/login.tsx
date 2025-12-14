import { createSignal } from "solid-js";
import Page from "../components/shared/layout/page";
import { authAPI } from "../utils/api";

export default function Login() {
  const [password, setPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!password()) {
      setError("Password required");
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.login(password());
    } catch {
      setError("Authentication failed");
    } finally {
      window.location.href = "/";
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
                autocomplete="current-password"
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
              {isLoading() ? "Signing in..." : "Continue"}
            </button>
          </form>
        </div>
      </div>
    </Page>
  );
}
