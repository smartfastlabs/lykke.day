import { A } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";

export default function ResetPassword() {
  return (
    <ModalPage subtitle="Use your phone to sign in.">
      <div class="space-y-6 text-center">
        <div class="space-y-2">
          <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
            password reset
          </p>
          <p class="text-lg font-semibold text-stone-800">Use SMS to sign in</p>
        </div>
        <p class="text-stone-600 text-sm leading-relaxed">
          We've moved to phone-based sign-in. Enter your phone number and we'll
          text you a code to sign in—no password needed.
        </p>
        <div class="space-y-2 text-sm text-stone-600">
          <A
            href="/forgot-password"
            class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
          >
            Get a login code
          </A>
          <div>
            or{" "}
            <A
              href="/login"
              class="text-amber-700 font-semibold hover:text-amber-800 transition-colors"
            >
              sign in
            </A>
          </div>
        </div>
      </div>
    </ModalPage>
  );
}
