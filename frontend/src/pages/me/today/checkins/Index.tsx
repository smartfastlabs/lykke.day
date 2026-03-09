import { useNavigate } from "@solidjs/router";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { Component } from "solid-js";
import CheckInForm from "@/components/checkins/CheckInForm";
import SettingsPage from "@/components/shared/SettingsPage";

const TodayCheckInsPage: Component = () => {
  const navigate = useNavigate();

  return (
    <SettingsPage
      heading="Today's Check-Ins"
      actionButtons={[
        {
          label: "New Check-In",
          icon: faPlus,
          onClick: () => navigate("/me/checkin"),
        },
      ]}
    >
      <div class="rounded-2xl border border-white/70 bg-white/70 p-5 shadow-lg shadow-amber-900/5 backdrop-blur-sm">
        <p class="mb-4 text-sm text-stone-600">
          Add a quick check-in with optional text and any status signal ratings.
        </p>
        <CheckInForm />
      </div>
    </SettingsPage>
  );
};

export default TodayCheckInsPage;
