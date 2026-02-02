import { Component, Show, createSignal } from "solid-js";
import { A } from "@solidjs/router";
import SEO from "@/components/shared/SEO";
import Footer from "@/components/shared/layout/Footer";
import {
  PhoneInput,
  SubmitButton,
  FormError,
  type CountryCode,
  COUNTRY_CONFIGS,
} from "@/components/forms";
import { Quote } from "@/components/shared/Quote";
import { useAuth } from "@/providers/auth";
import { marketingAPI } from "@/utils/api";
import { usePageAnimation } from "@/utils/navigation";

const Landing: Component = () => {
  const { isAuthenticated } = useAuth();
  const mounted = usePageAnimation("landing");

  const [country, setCountry] = createSignal<CountryCode>("US");
  const [phoneNumber, setPhoneNumber] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [success, setSuccess] = createSignal(false);

  const AccountLink: Component = () => (
    <a
      href={isAuthenticated() ? "/me/today" : "/login"}
      class="absolute top-6 right-6 z-20 px-4 py-2 rounded-full bg-white/80 border border-stone-200 text-sm font-medium text-stone-700 shadow-sm hover:bg-white transition-colors"
    >
      {isAuthenticated() ? "My LYKKE" : "Log in"}
    </a>
  );

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const value = phoneNumber().trim();
    const digits = value.replace(/\D/g, "");
    const config = COUNTRY_CONFIGS[country()];

    if (!value) {
      setError("Please enter a phone number.");
      return;
    }
    if (digits.length < config.digitsMin) {
      setError(`Please enter a valid ${config.label} phone number.`);
      return;
    }

    const e164 = `+${config.dialCode}${digits}`;

    setError("");
    setIsLoading(true);

    try {
      await marketingAPI.requestEarlyAccess({ phone_number: e164 });
      setSuccess(true);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Please enter a valid phone number.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <SEO
        title="Lykke — Find happiness in everyday moments"
        description="Lykke (loo-kah) — the Danish art of finding happiness in everyday moments. A daily companion for people who struggle with the basics and want calmer, more consistent days."
        path="/"
      />
      <div class="min-h-screen relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

        <AccountLink />

        <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
        <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />
        <div class="absolute top-1/2 left-1/3 w-32 h-32 bg-gradient-to-r from-yellow-200/20 to-orange-200/20 rounded-full blur-2xl" />

        <div class="relative z-10 flex flex-col items-center px-6 py-20 md:py-28">
          <div class="max-w-3xl w-full text-center">
            <div
              class="mb-16 transition-all duration-1000 ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(-20px)",
              }}
            >
              <h1 class="text-4xl md:text-4xl lg:text-8xl font-bold tracking-tight text-stone-800 mb-4">
                lykke
                <span class="text-amber-500">.</span>
                day
              </h1>
            </div>

            <div
              class="mb-10 transition-all duration-1000 delay-200 ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <div class="inline-block bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl px-10 py-8 shadow-xl shadow-amber-900/5">
                <p
                  class="text-stone-700 text-xl md:text-2xl italic leading-relaxed mb-3"
                  style={{
                    "font-family": "'Cormorant Garamond', Georgia, serif",
                  }}
                >
                  Lykke
                  <span class="text-stone-400 not-italic text-lg">(n.)</span> —
                  the Danish art of finding happiness in everyday moments.
                </p>
                <p class="text-stone-400 text-sm tracking-wide uppercase">
                  pronounced: loo-kah
                </p>
              </div>
            </div>

            <div
              class="mt-10 mb-16 transition-all duration-1000 delay-[400ms] ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <div class="max-w-2xl mx-auto">
                <div class="my-12">
                  <p class="text-xl uppercase tracking-[0.25em] text-amber-700/80 mb-3">
                    A daily companion for adulting.
                  </p>
                </div>

                <Show
                  when={!success()}
                  fallback={
                    <div class="text-center">
                      <p class="text-stone-800 font-semibold mb-1.5">
                        You&apos;re in.
                      </p>
                    </div>
                  }
                >
                  <form
                    onSubmit={handleSubmit}
                    class="inline-flex flex-col gap-3 items-stretch"
                  >
                    <div class="flex flex-wrap gap-3 items-center justify-center">
                      <select
                        id="country"
                        value={country()}
                        onChange={(e) => {
                          setCountry(e.currentTarget.value as CountryCode);
                          setPhoneNumber("");
                          setError("");
                        }}
                        class="px-3 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
                        aria-label="Country"
                      >
                        {(Object.keys(COUNTRY_CONFIGS) as CountryCode[]).map(
                          (code) => (
                            <option value={code}>
                              {COUNTRY_CONFIGS[code].label} +
                              {COUNTRY_CONFIGS[code].dialCode}
                            </option>
                          ),
                        )}
                      </select>
                      <PhoneInput
                        id="phone-number"
                        country={country()}
                        value={phoneNumber}
                        onChange={(value) => {
                          setPhoneNumber(value);
                          setError("");
                        }}
                      />
                    </div>
                    <SubmitButton
                      isLoading={isLoading()}
                      loadingText="Sending..."
                      text="Get Started"
                    />

                    <div class="mt-3">
                      <FormError error={error()} />
                    </div>

                    <p class="mt-4 text-stone-400 text-xs text-center">
                      We only text about lykke.day. Unsubscribe anytime.
                    </p>
                  </form>
                </Show>

                <div class="mt-10">
                  <Quote
                    quote="There is more to life than simply increasing its speed."
                    author="Mahatma Gandhi"
                    containerClass="max-w-2xl mx-auto"
                    quoteClass="text-stone-600 text-base md:text-lg italic leading-relaxed px-6 text-center"
                  />
                </div>

                <div class="mt-8 text-center">
                  <A
                    href="/resources"
                    class="text-stone-600 text-base md:text-lg underline decoration-amber-400 underline-offset-4 hover:text-stone-800 transition-colors"
                  >
                    Not ready? Check out our collection of resources.
                  </A>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="relative z-10">
          <Footer />
        </div>
      </div>
    </>
  );
};

export default Landing;
