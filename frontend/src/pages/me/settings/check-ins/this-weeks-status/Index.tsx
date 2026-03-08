import { Component } from "solid-js";
import CheckInUseCaseConfigPage from "@/pages/me/settings/check-ins/UseCaseConfig";

const ThisWeeksStatusCheckInConfigPage: Component = () => (
  <CheckInUseCaseConfigPage
    heading="This Week's Status Check-In"
    usecase="this_weeks_status"
    successMessage="This week's status check-in settings saved successfully"
    amendmentsDescription="Add custom instructions that will be appended to the default this week's status check-in prompt."
  />
);

export default ThisWeeksStatusCheckInConfigPage;
