import { Component, type JSX } from "solid-js";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
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
import type { TaskCategory, TaskType } from "../../types/api";

interface IconProps {
  icon?: IconDefinition;
  key?: string;
  class?: string;
}

export function Icon(props: IconProps): JSX.Element {
  const icon = props.icon || getIcon(props.key || "") || getIcon("square");
  if (!icon) {
    return <></>;
  }
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

interface CategoryIconProps {
  category: TaskCategory;
}

export function CategoryIcon(props: CategoryIconProps): JSX.Element {
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

interface TypeIconProps {
  type: TaskType;
}

export function TypeIcon(props: TypeIconProps): JSX.Element {
  return <Icon icon={typeIcons[props.type]} />;
}
