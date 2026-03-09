import { Component } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { faSquareCheck } from "@fortawesome/free-solid-svg-icons";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { Icon } from "@/components/shared/Icon";
import CheckInForm from "@/components/checkins/CheckInForm";

const CheckInPage: Component = () => {
  const navigate = useNavigate();

  return (
    <>
      <ModalPage
        subtitle="Add a check-in for today"
        title={
          <div class="flex items-center justify-center gap-3">
            <Icon icon={faSquareCheck} class="w-6 h-6 fill-amber-600" />
            <p class="text-2xl font-semibold text-stone-800">Add Check-In</p>
          </div>
        }
      >
        <CheckInForm
          submitText="Save & return"
          loadingText="Saving..."
          onSuccess={() => navigate("/me/today")}
          onCancel={() => navigate("/me/today")}
        />
      </ModalPage>
      <FloatingActionButtons />
    </>
  );
};

export default CheckInPage;
