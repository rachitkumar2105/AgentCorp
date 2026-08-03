export interface User {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  organization_id?: number | null;
  permissions?: string[];
}
