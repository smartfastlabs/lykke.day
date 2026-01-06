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
  faCookie,
  faPhone,
  faDumbbell as faExercise,
  faUsers as faSocial,
  faPeopleGroup,
  faSoap,
  faShirt,
  faFilm,
  faGamepad as faHobby,
  faGraduationCap as faLearning,
  faBook as faStudy,
  faBookOpen as faReading,
  faCar as faCommute,
  faPlane as faTravel,
  faCalendarCheck,
  faToolbox,
  faEnvelope,
  faMoneyBill,
  faCreditCard as faPayment,
  faScrewdriverWrench,
  faClipboard,
  faLaptop as faTechnology,
  faMobileScreen,
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
  // Eating & Meals
  MEAL: faBowlFood,
  SNACK: faCookie,
  // Work & Professional
  WORK: faBriefcase,
  MEETING: faHandshake,
  CALL: faPhone,
  // Exercise & Fitness
  EXERCISE: faExercise,
  WORKOUT: faDumbbell,
  // Social & Events
  EVENT: faCalendar,
  SOCIAL: faSocial,
  GATHERING: faPeopleGroup,
  // Household Tasks
  CHORE: faBroom,
  CLEANING: faBroom,
  LAUNDRY: faShirt,
  // Errands & Shopping
  ERRAND: faBasketShopping,
  SHOPPING: faShoppingCart,
  // Personal Care
  PERSONAL_CARE: faDroplet,
  GROOMING: faScissors,
  // Entertainment & Leisure
  ACTIVITY: faPersonWalking,
  ENTERTAINMENT: faFilm,
  HOBBY: faHobby,
  // Learning & Education
  LEARNING: faLearning,
  STUDY: faStudy,
  READING: faReading,
  // Transportation
  COMMUTE: faCommute,
  TRAVEL: faTravel,
  // Appointments & Services
  APPOINTMENT: faCalendarCheck,
  SERVICE: faToolbox,
  // Communication
  COMMUNICATION: faEnvelope,
  EMAIL: faEnvelope,
  // Financial
  FINANCIAL: faMoneyBill,
  PAYMENT: faPayment,
  // Maintenance & Repairs
  MAINTENANCE: faScrewdriverWrench,
  REPAIR: faWrench,
  // Planning & Organization
  PLANNING: faClipboard,
  ORGANIZATION: faFolderOpen,
  // Technology
  TECHNOLOGY: faTechnology,
  DIGITAL: faMobileScreen,
};

export function getTypeIcon(type?: TaskType): IconDefinition | null {
  if (!type) return null;
  return typeIcons[type] ?? null;
}
