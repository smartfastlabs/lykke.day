import { Component } from "solid-js";
import { Dynamic } from "solid-js/web";
import {
  clock,
  checkCircle,
  arrowRight,
  exclamationTriangle,
  xCircle,
  arrowPath,
} from "solid-heroicons/outline";
import { Icon } from "solid-heroicons";

export type TaskStatusType =
  | "PENDING" // Waiting to be done
  | "COMPLETED" // Done successfully
  | "SKIPPED" // User chose not to do it
  | "BLOCKED" // Couldn’t do it for a reason (sick, weather, etc.)
  | "MISSED" // Missed deadline or forgot
  | "DEFERRED"; // Moved to a later time/day

interface TaskStatusBadgeProps {
  status: TaskStatusType;
}

const statusConfig: Record<
  TaskStatusType,
  { label: string; color: string; icon: any }
> = {
  NOT_READY: {
    label: "Pending",
    color: "text-yellow-700 bg-yellow-50 border-yellow-200",
    icon: clock,
  },
  READY: {
    label: "Pending",
    color: "text-yellow-700 bg-yellow-50 border-yellow-200",
    icon: clock,
  },
  PENDING: {
    label: "Pending",
    color: "text-yellow-700 bg-yellow-50 border-yellow-200",
    icon: clock,
  },
  COMPLETED: {
    label: "Completed",
    color: "text-[#A0DFA2]",
    icon: checkCircle,
  },
  SKIPPED: {
    label: "Skipped",
    color: "text-gray-700",
    icon: arrowRight,
  },
  BLOCKED: {
    label: "Blocked",
    color: "text-red-700",
    icon: exclamationTriangle,
  },
  MISSED: {
    label: "Missed",
    color: "text-orange-700",
    icon: xCircle,
  },
  DEFERRED: {
    label: "Deferred",
    color: "text-blue-700",
    icon: arrowPath,
  },
};

const TaskStatusBadge: Component<TaskStatusBadgeProps> = (props) => {
  const cfg = () => statusConfig[props.status];
  console.log(props.status);

  return <Icon path={cfg().icon} class={`w-8 h-8 ${cfg().color}`} />;
};

export default TaskStatusBadge;
