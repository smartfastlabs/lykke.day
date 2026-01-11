import { Component } from "solid-js";
import Footer from "@/components/shared/layout/Footer";

const Terms: Component = () => {
  return (
    <div class="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex flex-col">
      <div class="max-w-2xl mx-auto px-6 py-16 flex-1">
        <h1 class="text-3xl font-bold text-stone-800 mb-2">Terms of Service</h1>
        <p class="text-stone-500 text-sm mb-10">Last updated: January 2026</p>

        <div class="space-y-8 text-stone-700 leading-relaxed">
          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              The Basics
            </h2>
            <p>
              By using lykke.day, you agree to these terms. We provide a daily
              planning and wellness companion — use it kindly and lawfully.
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              Your Account
            </h2>
            <ul class="list-disc list-inside space-y-2 ml-2">
              <li>You're responsible for keeping your login secure</li>
              <li>One account per person</li>
              <li>You must be 13 or older to use lykke.day</li>
            </ul>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">
              Your Content
            </h2>
            <p>
              Everything you create in lykke.day belongs to you. We don't claim
              ownership of your tasks, plans, or any content you add. You grant
              us permission to store and display your content back to you — 
              nothing more.
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">Our Role</h2>
            <p>
              We strive to keep lykke.day running smoothly, but we can't
              guarantee it will always be available or error-free. We're not
              liable for any decisions you make based on the app. Use your own
              judgment.
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">Fair Use</h2>
            <p>Don't use lykke.day to:</p>
            <ul class="list-disc list-inside space-y-2 ml-2 mt-2">
              <li>Break the law or help others do so</li>
              <li>Harass, spam, or harm others</li>
              <li>Attempt to access accounts that aren't yours</li>
              <li>Overload or disrupt the service</li>
            </ul>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">Changes</h2>
            <p>
              We may update these terms occasionally. Continued use after
              changes means you accept them. We'll notify you of significant
              changes via email.
            </p>
          </section>

          <section>
            <h2 class="text-lg font-semibold text-stone-800 mb-3">Contact</h2>
            <p>
              Questions? Reach us at{" "}
              <a
                href="mailto:hello@lykke.day"
                class="text-amber-700 hover:underline"
              >
                hello@lykke.day
              </a>
            </p>
          </section>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Terms;

