import { useNavigate } from "@solidjs/router";
import { Component } from "solid-js";
import {
  faRightFromBracket,
  faGear,
  faHouse,
  faTerminal,
} from "@fortawesome/free-solid-svg-icons";

import LinkGrid, { LinkItem } from "@/components/shared/LinkGrid";
import { authAPI } from "@/utils/api";

const NavPage: Component = () => {
  const navigate = useNavigate();

  const navItems: LinkItem[] = [
    { label: "Home", icon: faHouse, url: "/me" },
    { label: "Commands", icon: faTerminal, url: "/me/nav/commands" },
    { label: "Settings", icon: faGear, url: "/me/settings" },
    {
      label: "Logout",
      icon: faRightFromBracket,
      method: async () => {
        await authAPI.logout();
        navigate("/login");
      },
    },
  ];

  return <LinkGrid items={navItems} />;
};

export default NavPage;
