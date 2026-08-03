import { request } from '../http';
import type { Goal, GoalCreate } from '../types/goal';
import type { Execution } from '../types/agent';

export async function createGoal(payload: GoalCreate, organizationId: number): Promise<Goal> {
  return request<Goal>(`/api/v1/agent/goals?organization_id=${organizationId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getGoal(goalId: number, organizationId: number): Promise<Goal> {
  return request<Goal>(`/api/v1/agent/goals/${goalId}?organization_id=${organizationId}`);
}

export async function getGoals(organizationId: number): Promise<Goal[]> {
  // Return empty array since backend list goals endpoint is not directly exposed
  return [];
}

export async function executeGoal(goalId: number, organizationId: number): Promise<Execution> {
  return request<Execution>(`/api/v1/agent/goals/${goalId}/execute?organization_id=${organizationId}`, {
    method: 'POST',
  });
}
