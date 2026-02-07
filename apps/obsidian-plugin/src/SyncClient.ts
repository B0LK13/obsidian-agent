/**
 * WebSocket sync client for communication with PKM Agent backend.
 */

export enum SyncEventType {
    FILE_CREATED = "file_created",
    FILE_MODIFIED = "file_modified",
    FILE_DELETED = "file_deleted",
    FILE_RENAMED = "file_renamed",
    NOTE_INDEXED = "note_indexed",
    INDEX_UPDATED = "index_updated",
    SYNC_REQUEST = "sync_request",
    SYNC_RESPONSE = "sync_response",
    SYNC_ERROR = "sync_error",
    HEARTBEAT = "heartbeat",
    HEALTH_CHECK = "health_check",
}

export interface SyncEvent {
    event_id?: string;
    event_type: SyncEventType | string;
    timestamp?: number;
    source?: string;
    data?: Record<string, any>;
    metadata?: Record<string, any>;
}

export interface SyncClientConfig {
    url: string;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

type EventHandler = (event: SyncEvent) => void;

export class SyncClient {
    private ws: WebSocket | null = null;
    private config: SyncClientConfig;
    private handlers: Map<string, EventHandler[]> = new Map();
    private reconnectAttempts = 0;
    private reconnectTimer: number | null = null;
    private isConnecting = false;

    constructor(config: SyncClientConfig) {
        this.config = {
            reconnectInterval: 5000,
            maxReconnectAttempts: 10,
            ...config,
        };
    }

    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
            return;
        }

        this.isConnecting = true;

        try {
            this.ws = new WebSocket(this.config.url);

            this.ws.onopen = () => {
                console.log('SyncClient: Connected to', this.config.url);
                this.isConnecting = false;
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data) as SyncEvent;
                    this.handleEvent(data);
                } catch (error) {
                    console.error('SyncClient: Failed to parse message', error);
                }
            };

            this.ws.onclose = () => {
                console.log('SyncClient: Disconnected');
                this.isConnecting = false;
                this.scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('SyncClient: WebSocket error', error);
                this.isConnecting = false;
            };
        } catch (error) {
            console.error('SyncClient: Failed to connect', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 10)) {
            console.log('SyncClient: Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.config.reconnectInterval || 5000;

        console.log(`SyncClient: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        this.reconnectTimer = window.setTimeout(() => {
            this.connect();
        }, delay);
    }

    private handleEvent(event: SyncEvent): void {
        const eventType = event.event_type;
        const handlers = this.handlers.get(eventType) || [];

        for (const handler of handlers) {
            try {
                handler(event);
            } catch (error) {
                console.error('SyncClient: Handler error', error);
            }
        }

        const wildcardHandlers = this.handlers.get('*') || [];
        for (const handler of wildcardHandlers) {
            try {
                handler(event);
            } catch (error) {
                console.error('SyncClient: Wildcard handler error', error);
            }
        }
    }

    on(eventType: SyncEventType | string, handler: EventHandler): void {
        const handlers = this.handlers.get(eventType) || [];
        handlers.push(handler);
        this.handlers.set(eventType, handlers);
    }

    off(eventType: SyncEventType | string, handler: EventHandler): void {
        const handlers = this.handlers.get(eventType) || [];
        const index = handlers.indexOf(handler);
        if (index >= 0) {
            handlers.splice(index, 1);
            this.handlers.set(eventType, handlers);
        }
    }

    async sendEvent(event: Partial<SyncEvent>): Promise<void> {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('SyncClient: Not connected, cannot send event');
            return;
        }

        const fullEvent: SyncEvent = {
            event_id: crypto.randomUUID(),
            timestamp: Date.now() / 1000,
            source: 'obsidian',
            ...event,
            event_type: event.event_type || 'unknown',
        };

        this.ws.send(JSON.stringify(fullEvent));
    }

    get isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}
