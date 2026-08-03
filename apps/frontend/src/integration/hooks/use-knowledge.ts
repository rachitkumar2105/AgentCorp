import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { createKnowledgeBase, getKnowledgeBases, uploadDocument, listDocuments, getDocument, deleteDocument } from '../api/knowledge';

export function useKnowledge(organizationId: number) {
  const queryClient = useQueryClient();

  const kbListQuery = useQuery({
    queryKey: queryKeys.knowledge.list(organizationId),
    queryFn: () => getKnowledgeBases(organizationId),
    enabled: Boolean(organizationId),
  });

  const createKbMutation = useMutation({
    mutationFn: (payload: { name: string; description?: string; visibility: string }) => createKnowledgeBase(payload, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledge.list(organizationId) });
    },
  });

  return {
    knowledgeBases: kbListQuery.data ?? [],
    isLoadingBases: kbListQuery.isLoading,
    createKnowledgeBase: (payload: { name: string; description?: string; visibility: string }) => createKbMutation.mutateAsync(payload),
    isCreatingBase: createKbMutation.isPending,
  };
}

export function useKnowledgeDocuments(knowledgeBaseId: number, organizationId: number) {
  const queryClient = useQueryClient();

  const docsQuery = useQuery({
    queryKey: queryKeys.knowledge.documents(knowledgeBaseId, organizationId),
    queryFn: () => listDocuments(knowledgeBaseId, organizationId),
    enabled: Boolean(knowledgeBaseId) && Boolean(organizationId),
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, duplicatePolicy }: { file: File; duplicatePolicy?: string }) => uploadDocument(knowledgeBaseId, organizationId, file, duplicatePolicy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledge.documents(knowledgeBaseId, organizationId) });
    },
  });

  return {
    documents: docsQuery.data ?? [],
    isLoadingDocuments: docsQuery.isLoading,
    uploadDocument: (file: File, duplicatePolicy?: string) => uploadMutation.mutateAsync({ file, duplicatePolicy }),
    isUploading: uploadMutation.isPending,
  };
}

export function useKnowledgeDocument(documentId: number, organizationId: number) {
  const queryClient = useQueryClient();

  const docQuery = useQuery({
    queryKey: queryKeys.knowledge.documentDetail(documentId, organizationId),
    queryFn: () => getDocument(documentId, organizationId),
    enabled: Boolean(documentId) && Boolean(organizationId),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteDocument(documentId, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledge.documentDetail(documentId, organizationId) });
    },
  });

  return {
    document: docQuery.data ?? null,
    isLoading: docQuery.isLoading,
    deleteDocument: () => deleteMutation.mutateAsync(),
    isDeleting: deleteMutation.isPending,
  };
}
