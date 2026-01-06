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
  faScissors,
  faMoon as faSleep,
  faDumbbell as faFitness,
  faStethoscope,
  faCookieBite,
  faBroom,
  faWrench,
  faFolderOpen,
  faBriefcase as faWork,
  faHandshake,
  faUserGroup,
  faHeart as faRelationship,
  faShoppingCart,
  faCar,
  faLaptop,
  faGamepad,
  faBookOpen,
  faDollarSign,
  faCreditCard,
  faComputer,
  faClipboardList,
  faFileInvoice,
  // Task type icons
  faBowlFood,
  faHandshake,
  faFilm,
  faCalendarCheck,
  faEnvelope,
  faMoneyBill,
  faClipboard,
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
  // Personal Care
  HYGIENE: faDroplet,
  GROOMING: faScissors,
  SLEEP: faSleep,
  // Health & Fitness
  HEALTH: faHeartPulse,
  FITNESS: faFitness,
  MEDICAL: faStethoscope,
  // Nutrition
  NUTRITION: faUtensils,
  COOKING: faCookieBite,
  // Home & Household
  HOUSE: faHouse,
  CLEANING: faBroom,
  MAINTENANCE: faWrench,
  ORGANIZATION: faFolderOpen,
  // Work & Professional
  WORK: faWork,
  MEETING: faHandshake,
  PROFESSIONAL: faBriefcase,
  // Social & Family
  FAMILY: faUserGroup,
  SOCIAL: faUsers,
  RELATIONSHIP: faRelationship,
  // Shopping & Errands
  SHOPPING: faShoppingCart,
  ERRAND: faShoppingCart,
  // Transportation
  COMMUTE: faCar,
  TRAVEL: faPlane,
  // Entertainment & Leisure
  ENTERTAINMENT: faGamepad,
  HOBBY: faGamepad,
  RECREATION: faUmbrellaBeach,
  // Education & Learning
  EDUCATION: faGraduationCap,
  LEARNING: faBookOpen,
  // Finance & Bills
  FINANCE: faDollarSign,
  BILLS: faCreditCard,
  // Technology & Digital
  TECHNOLOGY: faLaptop,
  DIGITAL: faComputer,
  // Pet Care
  PET: faPaw,
  // Other
  PLANNING: faClipboardList,
  ADMIN: faFileInvoice,
};

export function getCategoryIcon(category?: TaskCategory): IconDefinition | null {
  if (!category) return null;
  return categoryIcons[category] ?? null;
}

// Task Type icons
const typeIcons: Record<TaskType, IconDefinition> = {
  MEAL: faBowlFood,
  WORK: faBriefcase,
  MEETING: faHandshake,
  EXERCISE: faDumbbell,
  EVENT: faCalendar,
  SOCIAL: faUsers,
  CHORE: faBroom,
  ERRAND: faBasketShopping,
  SHOPPING: faShoppingCart,
  PERSONAL_CARE: faDroplet,
  ACTIVITY: faPersonWalking,
  ENTERTAINMENT: faFilm,
  LEARNING: faGraduationCap,
  COMMUTE: faCar,
  TRAVEL: faPlane,
  APPOINTMENT: faCalendarCheck,
  COMMUNICATION: faEnvelope,
  FINANCIAL: faMoneyBill,
  MAINTENANCE: faWrench,
  PLANNING: faClipboard,
  TECHNOLOGY: faLaptop,
};

export function getTypeIcon(type?: TaskType): IconDefinition | null {
  if (!type) return null;
  return typeIcons[type] ?? null;
}
