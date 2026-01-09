import { Component } from "solid-js";

const Footer: Component = () => {
  return (
    <footer class="py-8 px-6">
      <div class="max-w-3xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <p class="text-stone-400 text-sm">
          © {new Date().getFullYear()} lykke.day — All rights reserved.
        </p>
        <div class="flex items-center gap-6">
          <a
            href="/faq"
            class="text-stone-400 text-sm hover:text-stone-600 transition-colors"
          >
            FAQ
          </a>
          <a
            href="/privacy"
            class="text-stone-400 text-sm hover:text-stone-600 transition-colors"
          >
            Privacy
          </a>
          <a
            href="/terms"
            class="text-stone-400 text-sm hover:text-stone-600 transition-colors"
          >
            Terms
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

