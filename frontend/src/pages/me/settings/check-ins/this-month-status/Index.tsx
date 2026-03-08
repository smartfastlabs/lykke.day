import { Component } from "solid-js";
import CheckInUseCaseConfigPage from "@/pages/me/settings/check-ins/UseCaseConfig";

const ThisMonthStatusCheckInConfigPage: Component = () => (
  <CheckInUseCaseConfigPage
    heading="This Month's Status Check-In"
    usecase="this_month_status"
    successMessage="This month's status check-in settings saved successfully"
    amendmentsDescription="Add custom instructions that will be appended to the default this month's status check-in prompt."
  />
);

export default ThisMonthStatusCheckInConfigPage;
