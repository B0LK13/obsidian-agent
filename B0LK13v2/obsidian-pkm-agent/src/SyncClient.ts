/**
 * WebSocket Sync Client for Obsidian Plugin
 * 
 * Provides bidirectional real-time synchronization with Python backend.
 * Handles connection management, reconnection, and event broadcasting.
 */

import { Notice } from 'obsidian';

// ============================================
// TYPE DEFINITIONS
// ============================================

export enum SyncEventType {
    FILE_CREATED = 'file_created',
    FILE_MODIFIED = 'file_modified',
    FILE_DELETED = 'file_deleted',
    FILE_RENAMED = 'file_renamed',
    NOTE_INDEXED = 'note_indexed',
    EMBEDDING_UPDATED = 'embedding_updated',
    SYNC_REQUEST = 'sync_request',
    SYNC_RESPONSE = 'sync_response',
    SYNC_ERROR = 'sync_error',
    HEARTBEAT = 'heartbeat',
    CLIENT_CONNECTED = 'client_connected',
    CLIENT_DISCONNECTED = 'client_disconnected',
}

export interface SyncEvent {
    event_id: string;
    event_type: SyncEventType;
    timestamp: number;
    source: string;
    data: Record<string, any>;
    metadata?: Record<string, any>;
}

export type SyncEventHandler = (event: SyncEvent) => void | Promise<void>;

export interface SyncClientConfig {
    url?: string;
    reconnectMaxAttempts?: number;
    reconnectDelay?: number;
    heartbeatTimeout?: number;
    autoReconnect?: boolean;
}

export enum ConnectionState {
    DISCONNECTED = 'disconnected',
    CONNECTING = 'connecting',
    CONNECTED = 'connected',
    RECONNECTING = 'reconnecting',
    FAILED = 'failed',
}

// ============================================
// SYNC CLIENT
// ============================================

export class SyncClient {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private heartbeatTimer: NodeJS.Timeout | null = null;
    private lastHeartbeat: number = 0;
    private eventHandlers: Map<SyncEventType, Set<SyncEventHandler>> = new Map();
    private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
    
    private readonly url: string;
    private readonly reconnectMaxAttempts: number;
    private readonly reconnectDelay: number;
    private readonly heartbeatTimeout: number;
    private readonly autoReconnect: boolean;
    
    constructor(config: SyncClientConfig = {}) {
        this.url = config.url || 'ws://localhost:27125';
        this.reconnectMaxAttempts = config.reconnectMaxAttempts ?? 5;
        this.reconnectDelay = config.reconnectDelay ?? 2000;
        this.heartbeatTimeout = config.heartbeatTimeout ?? 45000; // 45 seconds
        this.autoReconnect = config.autoReconnect ?? true;
    }
    
    /**
     * Connect to sync server
     */
    connect(): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('SyncClient: Already connected');
            return;
        }
        
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            console.log('SyncClient: Connection in progress');
            return;
        }
        
        this.setState(ConnectionState.CONNECTING);
        console.log(`SyncClient: Connecting to ${this.url}`);
        
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = this.handleOpen.bind(this);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onerror = this.handleError.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
        } catch (error) {
            console.error('SyncClient: Failed to create WebSocket', error);
            this.setState(ConnectionState.FAILED);
            this.attemptReconnect();
        }
    }
    
    /**
     * Disconnect from sync server
     */
    disconnect(): void {
        console.log('SyncClient: Disconnecting...');
        
        this.clearTimers();
        
        if (this.ws) {
            // Disable auto-reconnect
            const wasAutoReconnect = this.autoReconnect;
            (this as any).autoReconnect = false;
            
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
            
            (this as any).autoReconnect = wasAutoReconnect;
        }
        
        this.setState(ConnectionState.DISCONNECTED);
    }
    
    /**
     * Send sync event to server
     */
    sendEvent(event: Partial<SyncEvent>): void {
        if (!this.isConnected()) {
            console.warn('SyncClient: Cannot send event, not connected');
            return;
        }
        
        const fullEvent: SyncEvent = {
            event_id: event.event_id || this.generateId(),
            event_type: event.event_type!,
            timestamp: event.timestamp || Date.now(),
            source: event.source || 'obsidian',
            data: event.data || {},
            metadata: event.metadata || {},
        };
        
        try {
            this.ws!.send(JSON.stringify(fullEvent));
            console.log(`SyncClient: Sent ${fullEvent.event_type}`, fullEvent.data);
        } catch (error) {
            console.error('SyncClient: Failed to send event', error);
        }
    }
    
    /**
     * Register event handler
     */
    on(eventType: SyncEventType, handler: SyncEventHandler): void {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, new Set());
        }
        
        this.eventHandlers.get(eventType)!.add(handler);
    }
    
    /**
     * Unregister event handler
     */
    off(eventType: SyncEventType, handler: SyncEventHandler): void {
        const handlers = this.eventHandlers.get(eventType);
        if (handlers) {
            handlers.delete(handler);
        }
    }
    
    /**
     * Register one-time event handler
     */
    once(eventType: SyncEventType, handler: SyncEventHandler): void {
        const wrappedHandler: SyncEventHandler = async (event) => {
            await handler(event);
            this.off(eventType, wrappedHandler);
        };
        
        this.on(eventType, wrappedHandler);
    }
    
    /**
     * Check if connected
     */
    isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }
    
    /**
     * Get connection state
     */
    getState(): ConnectionState {
        return this.connectionState;
    }
    
    /**
     * Request sync from server
     */
    async requestSync(resourceType: string, resourceId?: string): Promise<void> {
        this.sendEvent({
            event_type: SyncEventType.SYNC_REQUEST,
            data: {
                resource_type: resourceType,
                resource_id: resourceId,
            },
        });
    }
    
    // ============================================
    // PRIVATE METHODS
    // ============================================
    
    private handleOpen(event: Event): void {
        console.log('SyncClient: Connected');
        
        this.reconnectAttempts = 0;
        this.setState(ConnectionState.CONNECTED);
        this.startHeartbeatMonitor();
        
        new Notice('PKM Agent: Sync connected', 2000);
        
        // Trigger connected handlers
        this.emit({
            event_id: this.generateId(),
            event_type: SyncEventType.CLIENT_CONNECTED,
            timestamp: Date.now(),
            source: 'obsidian',
            data: {},
        });
    }
    
    private handleMessage(event: MessageEvent): void {
        try {
            const syncEvent: SyncEvent = JSON.parse(event.data);
            
            // Update heartbeat timer
            if (syncEvent.event_type === SyncEventType.HEARTBEAT) {
                this.lastHeartbeat = Date.now();
                console.log('SyncClient: Heartbeat received');
            }
            
            // Emit to registered handlers
            this.emit(syncEvent);
            
        } catch (error) {
            console.error('SyncClient: Failed to parse message', error);
        }
    }
    
    private handleError(event: Event): void {
        console.error('SyncClient: WebSocket error', event);
        
        if (this.connectionState === ConnectionState.CONNECTING) {
            this.setState(ConnectionState.FAILED);
        }
    }
    
    private handleClose(event: CloseEvent): void {
        console.log(`SyncClient: Connection closed (code: ${event.code}, reason: ${event.reason})`);
        
        this.clearTimers();
        this.ws = null;
        
        if (this.connectionState !== ConnectionState.DISCONNECTED) {
            this.setState(ConnectionState.DISCONNECTED);
            
            // Trigger disconnected handlers
            this.emit({
                event_id: this.generateId(),
                event_type: SyncEventType.CLIENT_DISCONNECTED,
                timestamp: Date.now(),
                source: 'obsidian',
                data: { code: event.code, reason: event.reason },
            });
            
            // Attempt reconnect if enabled
            if (this.autoReconnect) {
                this.attemptReconnect();
            } else {
                new Notice('PKM Agent: Sync disconnected', 3000);
            }
        }
    }
    
    private attemptReconnect(): void {
        if (this.reconnectAttempts >= this.reconnectMaxAttempts) {
            console.error('SyncClient: Max reconnection attempts reached');
            this.setState(ConnectionState.FAILED);
            new Notice('PKM Agent: Sync connection failed. Please check server.', 5000);
            return;
        }
        
        this.reconnectAttempts++;
        this.setState(ConnectionState.RECONNECTING);
        
        const delay = this.reconnectDelay * this.reconnectAttempts;
        
        console.log(`SyncClient: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.reconnectMaxAttempts})`);
        
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, delay);
    }
    
    private startHeartbeatMonitor(): void {
        this.lastHeartbeat = Date.now();
        
        this.heartbeatTimer = setInterval(() => {
            const timeSinceHeartbeat = Date.now() - this.lastHeartbeat;
            
            if (timeSinceHeartbeat > this.heartbeatTimeout) {
                console.warn('SyncClient: Heartbeat timeout, connection may be dead');
                
                // Force reconnect
                if (this.ws) {
                    this.ws.close();
                }
            }
        }, 10000); // Check every 10 seconds
    }
    
    private clearTimers(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
    
    private emit(event: SyncEvent): void {
        const handlers = this.eventHandlers.get(event.event_type);
        
        if (handlers && handlers.size > 0) {
            handlers.forEach(async (handler) => {
                try {
                    await handler(event);
                } catch (error) {
                    console.error(`SyncClient: Handler error for ${event.event_type}`, error);
                }
            });
        }
    }
    
    private setState(newState: ConnectionState): void {
        if (this.connectionState !== newState) {
            console.log(`SyncClient: State ${this.connectionState} -> ${newState}`);
            this.connectionState = newState;
        }
    }
    
    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
}
