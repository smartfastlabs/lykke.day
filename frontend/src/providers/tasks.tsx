import {
  createSignal,
  createContext,
  createResource,
  useContext,
  onMount,
} from "solid-js";

const TaskContext = createContext();

export function TaskProvider(props) {
  const [tasks, taskManager] = createResource<Any[]>(() => []);

  onMount(async () => {
    taskManager.mutate(await TaskService.getTasksForDate());
  });

  const updateTask = async (input: Any) => {
    taskManager.mutate((items) =>
      items.map((i) => (i.id !== input.id ? i : { ...i, ...input }))
    );
    return input;
  };

  const setTaskStatus = async (task: Any, status: Any) => {
    await updateTask(await TaskService.setTaskStatus(task, status));
  };

  const value = {
    tasks,
    updateTask,
    setTaskStatus,
  };

  return (
    <TaskContext.Provider value={value}>{props.children}</TaskContext.Provider>
  );
}

export function useTaskManager() {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error("useTaskManager must be used within a TaskProvider");
  }
  return context;
}
