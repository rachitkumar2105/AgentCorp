export interface RealtimeMessage {
  type: string;
  payload: any;
}

export interface RealtimeHandlers {
  onMessage?: (msg: RealtimeMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (err: any) => void;
}

export class RealtimeClient {
  private handlers: RealtimeHandlers = {};

  constructor(private organizationId: number) {}

  public connect(handlers: RealtimeHandlers): void {
    this.handlers = handlers;
    // Simulate initial connection sequence for future integration readiness
    console.log('[RealtimeClient] Connecting real-time foundation...', this.organizationId);
    setTimeout(() => {
      if (this.handlers.onConnect) {
        this.handlers.onConnect();
      }
    }, 100);
  }

  public disconnect(): void {
    console.log('[RealtimeClient] Disconnecting real-time foundation...');
    if (this.handlers.onDisconnect) {
      this.handlers.onDisconnect();
    }
  }

  public emit(event: string, payload: any): void {
    console.log('[RealtimeClient] Emit placeholder event:', event, payload);
  }
}
