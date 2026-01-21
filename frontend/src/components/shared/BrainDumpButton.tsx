import { useLocation, useNavigate } from "@solidjs/router";
import { Component } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBrain, faHouse } from "@fortawesome/free-solid-svg-icons";

const BrainDumpButton: Component = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleClick = () => {
    if (
      location.pathname === "/me/brain-dump" ||
      location.pathname === "/me/brain-dump/dump"
    ) {
      navigate("/me");
      return;
    }

    navigate("/me/brain-dump/dump");
  };

  const isOnHomeRoute =
    location.pathname === "/me" || location.pathname === "/me/today";
  const isOnBrainDumpDump = location.pathname === "/me/brain-dump/dump";

  return (
    <div class="fixed bottom-6 left-6 z-50 print:hidden">
      <div class="flex items-center gap-1 rounded-full bg-gray-600 p-1 text-white shadow-lg">
        {!isOnBrainDumpDump && (
          <button
            onClick={handleClick}
            class="flex h-9 w-9 items-center justify-center rounded-full transition-transform duration-150 ease-in-out hover:bg-gray-700 active:scale-95"
            aria-label="Brain dump"
          >
            <Icon icon={faBrain} class="h-5 w-5 fill-white" />
          </button>
        )}
        {!isOnHomeRoute && (
          <button
            onClick={() => navigate("/me")}
            class="flex h-9 w-9 items-center justify-center rounded-full transition-transform duration-150 ease-in-out hover:bg-gray-700 active:scale-95"
            aria-label="Go to home"
          >
            <Icon icon={faHouse} class="h-5 w-5 fill-white" />
          </button>
        )}
      </div>
    </div>
  );
};

export default BrainDumpButton;
