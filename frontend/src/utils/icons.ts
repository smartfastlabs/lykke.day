import { config, library } from "@fortawesome/fontawesome-svg-core";
import "@fortawesome/fontawesome-svg-core/styles.css";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faCoffee,
  faUser,
  faChartBar,
  faCogs,
  faBroom,
  faFaceSmileWink,
  faGrip,
  faGear,
  faGripVertical,
  faBriefcase,
  faCouch,
  faDumbbell,
  faPlane,
  faHouse,
  faUsers,
  faBook,
  faPalette,
  faHeart,
  faBed,
  faSun,
  faMoon,
  faUmbrellaBeach,
  faMugHot,
  faPersonRunning,
  faTree,
  faGraduationCap,
  faCakeCandles,
  faStar,
} from "@fortawesome/free-solid-svg-icons";

library.add(
  faGear,
  faGripVertical,
  faFaceSmileWink,
  faBroom,
  faCogs,
  faCoffee,
  faUser,
  faChartBar,
  faGrip,
  faBriefcase,
  faCouch,
  faDumbbell,
  faPlane,
  faHouse,
  faUsers,
  faBook,
  faPalette,
  faHeart,
  faBed,
  faSun,
  faMoon,
  faUmbrellaBeach,
  faMugHot,
  faPersonRunning,
  faTree,
  faGraduationCap,
  faCakeCandles,
  faStar
);

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
  focus: faStar,
};

config.autoAddCss = false;

export function getIcon(key: string): IconDefinition | null {
  return icons[key];
}