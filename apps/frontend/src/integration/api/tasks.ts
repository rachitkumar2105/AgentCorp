import type { Task } from '../types/task';

export async function getTasks(): Promise<Task[]> {
  return [];
}

export async function getTask(taskId: number): Promise<Task | null> {
  return null;
}
