import { env } from './env';
import { readStoredAuth } from './auth-storage';

export interface StreamHandlers {
  onToken: (token: string, provider?: string, model?: string) => void;
  onDone: (data: any) => void;
  onError: (error: Error) => void;
}

export class StreamConnection {
  private abortController: AbortController | null = null;
  private isConnecting = false;

  constructor(
    private path: string,
    private bodyPayload: any,
    private organizationId: number
  ) {}

  public async connect(handlers: StreamHandlers) {
    if (this.isConnecting) return;
    this.isConnecting = true;
    this.abortController = new AbortController();

    const auth = readStoredAuth();
    const url = `${env.apiBaseUrl}${this.path}?organization_id=${this.organizationId}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(auth?.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {}),
        },
        body: JSON.stringify(this.bodyPayload),
        signal: this.abortController.signal,
      });

      this.isConnecting = false;

      if (!response.ok) {
        throw new Error(`Streaming failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim();
          } else if (trimmed.startsWith('data:')) {
            const rawData = trimmed.slice(5).trim();
            try {
              const parsed = JSON.parse(rawData);
              if (currentEvent === 'token') {
                handlers.onToken(parsed.token || '', parsed.provider, parsed.model);
              } else if (currentEvent === 'done') {
                handlers.onDone(parsed);
              } else if (currentEvent === 'error') {
                handlers.onError(new Error(parsed.error || 'Streaming error'));
              }
            } catch (err) {
              // Ignore JSON parse errors for incomplete data lines
            }
          }
        }
      }
    } catch (error: any) {
      this.isConnecting = false;
      if (error.name !== 'AbortError') {
        handlers.onError(error);
      }
    }
  }

  public disconnect() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.isConnecting = false;
  }
}

export function streamChat(
  conversationId: number | null,
  payload: any,
  organizationId: number,
  handlers: StreamHandlers
): StreamConnection {
  const path = conversationId
    ? `/api/v1/chat/${conversationId}/stream`
    : '/api/v1/chat/stream';

  const connection = new StreamConnection(path, payload, organizationId);
  connection.connect(handlers);
  return connection;
}

export async function stopGeneration(conversationId: number, organizationId: number): Promise<void> {
  const auth = readStoredAuth();
  await fetch(`${env.apiBaseUrl}/api/v1/chat/${conversationId}/stream?organization_id=${organizationId}`, {
    method: 'DELETE',
    headers: {
      ...(auth?.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {}),
    },
  });
}
