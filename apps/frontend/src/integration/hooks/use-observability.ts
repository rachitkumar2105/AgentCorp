import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getSystemMetrics, getDiagnostics, getAuditLogs } from '../api/observability';

export function useObservability(organizationId?: number) {
  const metricsQuery = useQuery({
    queryKey: queryKeys.observability.metrics(),
    queryFn: getSystemMetrics,
  });

  const diagnosticsQuery = useQuery({
    queryKey: queryKeys.observability.diagnostics(),
    queryFn: getDiagnostics,
  });

  const auditLogsQuery = useQuery({
    queryKey: queryKeys.observability.auditLogs(organizationId),
    queryFn: () => getAuditLogs(0, 100, organizationId),
  });

  return {
    metrics: metricsQuery.data ?? null,
    diagnostics: diagnosticsQuery.data ?? null,
    auditLogs: auditLogsQuery.data ?? [],
    isLoading: metricsQuery.isLoading || diagnosticsQuery.isLoading || auditLogsQuery.isLoading,
    error: metricsQuery.error || diagnosticsQuery.error || auditLogsQuery.error,
  };
}
