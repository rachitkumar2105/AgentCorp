export interface Runtime {
  version: string;
  status: string;
  configured_providers?: string[];
  uptime?: number;
}
