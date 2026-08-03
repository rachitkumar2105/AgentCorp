import { request } from '../http';
import type { Workflow, WorkflowCreate, WorkflowExecution } from '../types/workflow';

export async function createWorkflow(payload: WorkflowCreate, organizationId: number): Promise<Workflow> {
  return request<Workflow>(`/api/v1/workflows?organization_id=${organizationId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function executeWorkflow(workflowId: number, organizationId: number, agentId: number): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(`/api/v1/workflows/${workflowId}/execute?organization_id=${organizationId}&agent_id=${agentId}`, {
    method: 'POST',
  });
}

export async function getWorkflowExecution(executionId: number, organizationId: number): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(`/api/v1/workflows/${executionId}?organization_id=${organizationId}`);
}
