import { Component } from "solid-js";
import {
  faUtensils,
  faDroplet,
  faPaw,
  faHeartPulse,
  faHouse,
  faBowlFood,
  faCalendar,
  faBroom,
  faBasketShopping,
  faPersonWalking,
} from "@fortawesome/free-solid-svg-icons";
import { getIcon } from "../../utils/icons";

export function Icon(props): Component {
  const icon = props.icon || getIcon(props.key) || getIcon("square");
  return (
    <svg
      viewBox={`0 0 ${icon.icon[0]} ${icon.icon[1]}`}
      class={props.class ?? "w-4 h-4 fill-gray-400"}
    >
      <path d={icon.icon[4] as string} />
    </svg>
  );
}

// Task Category icons
const categoryIcons: Record<TaskCategory, IconDefinition> = {
  NUTRITION: faUtensils,
  HYGIENE: faDroplet,
  PET: faPaw,
  HEALTH: faHeartPulse,
  HOUSE: faHouse,
};

export function CategoryIcon(props): Component {
  return <Icon icon={categoryIcons[props.category]} />;
}

// Task Type icons
const typeIcons: Record<TaskType, IconDefinition> = {
  MEAL: faBowlFood,
  EVENT: faCalendar,
  CHORE: faBroom,
  ERRAND: faBasketShopping,
  ACTIVITY: faPersonWalking,
};

export function TypeIcon(props): Component {
  return <Icon icon={typeIcons[props.type]} />;
}
