import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  // General icons
  faBriefcase,
  faCouch,
  faDumbbell,
  faPlane,
  faHouse,
  faUsers,
  faBook,
  faSquare,
  faPalette,
  faHeart,
  faBed,
  faSun,
  faMoon,
  faCalendar,
  faUmbrellaBeach,
  faMugHot,
  faPersonRunning,
  faTree,
  faGraduationCap,
  faCakeCandles,
  faClock,
  faStar,
  faCheckSquare,
  faPlus,
  faGripVertical,
  // Task category icons
  faUtensils,
  faDroplet,
  faPaw,
  faHeartPulse,
  // Task type icons
  faBowlFood,
  faBroom,
  faBasketShopping,
  faPersonWalking,
} from "@fortawesome/free-solid-svg-icons";

import type { TaskCategory, TaskType } from "@/types/api";

// General purpose icons by key name
export const icons: Record<string, IconDefinition> = {
  work: faBriefcase,
  relax: faCouch,
  gym: faDumbbell,
  travel: faPlane,
  home: faHouse,
  social: faUsers,
  reading: faBook,
  creative: faPalette,
  wellness: faHeart,
  sleep: faBed,
  morning: faSun,
  evening: faMoon,
  vacation: faUmbrellaBeach,
  cozy: faMugHot,
  exercise: faPersonRunning,
  nature: faTree,
  learning: faGraduationCap,
  celebration: faCakeCandles,
  clock: faClock,
  focus: faStar,
  checkMark: faCheckSquare,
  square: faSquare,
  calendar: faCalendar,
  plus: faPlus,
  gripVertical: faGripVertical,
};

export function getIcon(key: string): IconDefinition | null {
  return icons[key] ?? null;
}

// Task Category icons
const categoryIcons: Record<TaskCategory, IconDefinition> = {
  NUTRITION: faUtensils,
  HYGIENE: faDroplet,
  PET: faPaw,
  HEALTH: faHeartPulse,
  HOUSE: faHouse,
};

export function getCategoryIcon(category?: TaskCategory): IconDefinition | null {
  if (!category) return null;
  return categoryIcons[category] ?? null;
}

// Task Type icons
const typeIcons: Record<TaskType, IconDefinition> = {
  MEAL: faBowlFood,
  EVENT: faCalendar,
  CHORE: faBroom,
  ERRAND: faBasketShopping,
  ACTIVITY: faPersonWalking,
};

export function getTypeIcon(type?: TaskType): IconDefinition | null {
  if (!type) return null;
  return typeIcons[type] ?? null;
}
