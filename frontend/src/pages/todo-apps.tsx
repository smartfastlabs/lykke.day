import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const todoApps: MediaItem[] = [
  {
    title: "Notion",
    creator: "Notion Labs",
    summary:
      "All-in-one workspace blending notes, databases, tasks, and wikis—flexible building blocks that grow with how you think and work.",
    url: "https://www.notion.so",
    vibe: "flexible & powerful",
    thumbnail: "/images/todo-apps/notion.jpg",
  },
  {
    title: "Todoist",
    creator: "Doist",
    summary:
      "Clean, fast task manager with natural language input, priorities, and filters—turns messy to-dos into calm clarity.",
    url: "https://todoist.com",
    vibe: "streamlined focus",
    thumbnail: "/images/todo-apps/todoist.jpg",
  },
  {
    title: "Things 3",
    creator: "Cultured Code",
    summary:
      "Beautifully minimal GTD app for Apple devices—projects, areas, and today view make tasks feel light and approachable.",
    url: "https://culturedcode.com/things/",
    vibe: "elegant simplicity",
    thumbnail: "/images/todo-apps/things.jpg",
  },
  {
    title: "TickTick",
    creator: "Appest Inc.",
    summary:
      "Feature-packed task manager with calendars, habits, timers, and custom views—all the tools without the clutter.",
    url: "https://ticktick.com",
    vibe: "complete toolkit",
    thumbnail: "/images/todo-apps/ticktick.jpg",
  },
  {
    title: "Microsoft To Do",
    creator: "Microsoft",
    summary:
      "Simple daily planner with My Day focus, intelligent suggestions, and seamless Office integration—free and reliable.",
    url: "https://todo.microsoft.com",
    vibe: "daily essentials",
    thumbnail: "/images/todo-apps/microsoft-todo.jpg",
  },
  {
    title: "Any.do",
    creator: "Any.do",
    summary:
      "Task list meets calendar with voice entry, shared lists, and a gentle daily planning ritual—friendly momentum.",
    url: "https://www.any.do",
    vibe: "daily rhythm",
    thumbnail: "/images/todo-apps/anydo.jpg",
  },
  {
    title: "Asana",
    creator: "Asana, Inc.",
    summary:
      "Team project hub with task dependencies, timelines, and multiple views—scales from solo lists to complex workflows.",
    url: "https://asana.com",
    vibe: "team clarity",
    thumbnail: "/images/todo-apps/asana.jpg",
  },
  {
    title: "Trello",
    creator: "Atlassian",
    summary:
      "Visual boards and cards for kanban-style planning—drag-and-drop simplicity that makes projects feel organized and alive.",
    url: "https://trello.com",
    vibe: "visual flow",
    thumbnail: "/images/todo-apps/trello.jpg",
  },
];

const TodoApps: Component = () => {
  return (
    <MediaPage
      title="Great Todo Apps"
      subtitle="great todo apps"
      description="lykke.day isn't a todo app—there are already plenty of excellent ones. These tools excel at capturing tasks and checking boxes. We focus on something different: designing days that feel good to live."
      items={todoApps}
      linkText="Visit Site"
    />
  );
};

export default TodoApps;

