import { request } from '../http';
import type { User } from '../types/user';

export async function getUser(userId: number): Promise<User> {
  return request<User>(`/users/${userId}`);
}

export async function getUsers(): Promise<User[]> {
  return request<User[]>('/users');
}
