import type { JSX } from "solid-js";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { getIcon } from "../../utils/icons";

interface IconProps {
  /** Direct icon definition - takes precedence over key */
  icon?: IconDefinition;
  /** Icon key name from the icons registry */
  key?: string;
  /** CSS classes for the SVG element */
  class?: string;
}

/**
 * Renders an icon as an inline SVG.
 * 
 * Usage:
 * - With direct icon: <Icon icon={faCheck} />
 * - With key: <Icon key="checkMark" />
 * - With custom classes: <Icon key="plus" class="w-6 h-6 fill-blue-500" />
 */
export function Icon(props: IconProps): JSX.Element {
  const icon = props.icon ?? getIcon(props.key ?? "") ?? getIcon("square");
  
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
