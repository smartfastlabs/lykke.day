import { Component } from "solid-js";
import { A } from "@solidjs/router";

const Footer: Component = () => {
  return (
    <footer class="py-8 px-6">
      <div class="max-w-3xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <p class="text-stone-400 text-sm">
          © {new Date().getFullYear()} lykke.day — All rights reserved.
        </p>
        <div class="flex items-center gap-6">
          <A
            href="/faq"
            class="text-stone-400 text-sm hover:text-stone-600 transition-colors"
          >
            FAQ
          </A>
          <A
            href="/privacy"
            class="text-stone-400 text-sm hover:text-stone-600 transition-colors"
          >
            Privacy
          </A>
          <A
            href="/terms"
            class="text-stone-400 text-sm hover:text-stone-600 transition-colors"
          >
            Terms
          </A>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

