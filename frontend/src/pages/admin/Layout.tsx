import { Component, ParentProps } from "solid-js";
import { NavigationLayout } from "@/pages/me/navigation/Layout";

const AdminLayout: Component<ParentProps> = (props) => {
  return <NavigationLayout>{props.children}</NavigationLayout>;
};

export default AdminLayout;
