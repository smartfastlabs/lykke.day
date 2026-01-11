import { Component } from "solid-js";
import Footer from "@/components/shared/layout/Footer";

const Privacy: Component = () => {
  return (
    <div class="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex flex-col">
      <div class="max-w-2xl mx-auto px-6 py-16 flex-1">
        <h1 class="text-3xl font-bold text-stone-800 mb-2">Privacy Policy</h1>
        <p class="text-stone-500 text-sm mb-10">Last updated: January 2026</p>

        <div class="space-y-8 text-stone-700 leading-relaxed">
          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              The Short Version
            </h2>
            <p>
              Your data is yours. We collect only what's needed to run lykke.day
              and we never sell your information. You can export or delete your
              data anytime.
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              What We Collect
            </h2>
            <ul class="list-disc list-inside space-y-2 ml-2">
              <li>
                <strong>Account info</strong> — email and password to identify
                you
              </li>
              <li>
                <strong>Your content</strong> — tasks, routines, and plans you
                create
              </li>
              <li>
                <strong>Optional integrations</strong> — calendar data if you
                choose to connect external services
              </li>
              <li>
                <strong>Device info</strong> — only if you enable push
                notifications
              </li>
            </ul>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              How We Use It
            </h2>
            <p>
              We use your data to provide and improve lykke.day. That's it. We
              don't run ads, we don't build profiles, and we don't share your
              information with third parties except as needed to operate the
              service (like sending emails).
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              Your Rights
            </h2>
            <ul class="list-disc list-inside space-y-2 ml-2">
              <li>Access and export your data at any time</li>
              <li>Delete your account and all associated data</li>
              <li>Opt out of non-essential communications</li>
            </ul>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">Security</h2>
            <p>
              We use industry-standard encryption and security practices.
              Passwords are hashed and never stored in plain text. All
              connections use HTTPS.
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">Contact</h2>
            <p>
              Questions? Reach us at{" "}
              <a
                href="mailto:privacy@lykke.day"
                class="text-amber-700 hover:underline"
              >
                privacy@lykke.day
              </a>
            </p>
          </section>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Privacy;

