import { Component } from "solid-js";
import CheckInUseCaseConfigPage from "@/pages/me/settings/check-ins/UseCaseConfig";

const UserStatusUseCaseCheckInConfigPage: Component = () => (
  <CheckInUseCaseConfigPage
    heading="User Status Check-In"
    usecase="user_status_use_case"
    successMessage="User status check-in settings saved successfully"
    amendmentsDescription="Add custom instructions that will be appended to the default user status check-in prompt."
  />
);

export default UserStatusUseCaseCheckInConfigPage;
