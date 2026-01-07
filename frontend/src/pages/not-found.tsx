import { useNavigate } from "@solidjs/router";
import { Component } from "solid-js";
import Page from "@/components/shared/layout/page";

const NotFound: Component = () => {
  const navigate = useNavigate();

  return (
    <Page>
      <div class="flex-1 flex flex-col items-center justify-center px-5 mb-12">
        <div class="relative mb-8">
          <div class="text-[12rem] font-black leading-none tracking-tighter text-neutral-100 select-none">
            404
          </div>
        </div>

        <h1 class="text-2xl font-bold text-neutral-900 mb-2 text-center">
          This day wasn't planned for
        </h1>
        <p class="text-neutral-500 mb-8 text-center max-w-md">
          The page you're looking for doesn't exist or has been moved to a
          different schedule.
        </p>

        <div class="flex gap-3">
          <button
            onClick={() => navigate(-1)}
            class="px-5 py-2.5 text-sm font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition-colors"
          >
            Go Back
          </button>
          <button
            onClick={() => navigate("/")}
            class="px-5 py-2.5 text-sm font-medium text-white bg-neutral-900 hover:bg-neutral-800 rounded-lg transition-colors"
          >
            Back to Today
          </button>
        </div>
      </div>
    </Page>
  );
};

export default NotFound;
