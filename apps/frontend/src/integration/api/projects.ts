import type { Project } from '../types/project';

export async function getProjects(): Promise<Project[]> {
  // Return empty array since backend projects endpoint is unavailable
  return [];
}

export async function getProject(projectId: number): Promise<Project | null> {
  return null;
}
