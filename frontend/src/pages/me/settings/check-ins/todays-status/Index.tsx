import { Component } from "solid-js";
import CheckInUseCaseConfigPage from "@/pages/me/settings/check-ins/UseCaseConfig";

const TodaysStatusCheckInConfigPage: Component = () => (
  <CheckInUseCaseConfigPage
    heading="Today's Status Check-In"
    usecase="todays_status"
    successMessage="Today's status check-in settings saved successfully"
    amendmentsDescription="Add custom instructions that will be appended to the default today's status check-in prompt."
  />
);

export default TodaysStatusCheckInConfigPage;
