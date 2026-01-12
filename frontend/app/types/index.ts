// API Response Types
export interface ApiResponse<T> {
    data: T;
    error?: string;
    status: number;
}

export interface ContentItem {
    id: number;
    name: string;
    filename: string;
    size: string;
    status: "ready" | "processing" | "queued";
    resolution?: string;
    duration?: string;
    progress?: number;
    created_at?: string;
    updated_at?: string;
}

export interface Integration {
    id: string;
    name: string;
    platform: "youtube" | "linkedin" | "tiktok" | "instagram" | "twitter";
    icon: string;
    iconBg: string;
    iconColor: string;
    connected: boolean;
    status: "connected" | "inactive" | "awaiting_token";
    latency?: string;
    quota?: string;
    lastSync?: string;
    apiKey?: string;
    credentials?: Record<string, unknown>;
}

export interface DarkProfile {
    id: string;
    name: string;
    avatar: string;
    category: string;
    level: number;
    status: "active" | "suspended" | "pending";
    platforms?: string[];
    stats?: {
        followers: number;
        engagement: number;
        posts: number;
    };
}

export interface AutomationRule {
    id: string;
    name: string;
    enabled: boolean;
    status: "active" | "paused" | "failed";
    conditions: RuleCondition[];
    actions: RuleAction[];
    created_at: string;
    updated_at: string;
}

export interface RuleCondition {
    type: "viral_score" | "engagement" | "time" | "hashtag";
    operator: ">" | "<" | "==" | "contains";
    value: string | number;
}

export interface RuleAction {
    type: "crosspost" | "schedule" | "archive" | "notify";
    platform?: string;
    delay?: number;
    tags?: string[];
}

export interface User {
    id: string;
    name: string;
    email: string;
    role: "admin" | "user" | "viewer";
    avatar?: string;
    preferences?: UserPreferences;
}

export interface UserPreferences {
    theme: "light" | "dark" | "auto";
    language: string;
    timezone: string;
    notifications: {
        email: boolean;
        push: boolean;
        inApp: boolean;
    };
}

export interface UploadQueueItem {
    id: string;
    file: File;
    status: "queued" | "uploading" | "processing" | "complete" | "error";
    progress: number;
    error?: string;
}

// Component Props Types
export interface ToggleProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
    label?: string;
}

export interface FileListItemProps {
    file: ContentItem;
    onAction?: (action: "play" | "edit" | "delete", file: ContentItem) => void;
}

export interface IntegrationCardProps {
    integration: Integration;
    onToggle: (id: string, checked: boolean) => void;
    onConfigure?: (id: string) => void;
}

export interface HeaderProps {
    title: string;
    subtitle?: string;
    actions?: React.ReactNode;
    showSystemStatus?: boolean;
}

export interface SidebarProps {
    activePage?: string;
    user?: User;
    onNavigate?: (path: string) => void;
}

// Event Handler Types
export type FileActionHandler = (action: "play" | "edit" | "delete", file: ContentItem) => void;
export type IntegrationToggleHandler = (id: string, checked: boolean) => void;
export type NavigationHandler = (path: string) => void;

// Form Types
export interface LoginForm {
    email: string;
    password: string;
    remember: boolean;
}

export interface UploadForm {
    files: File[];
    tags?: string[];
    schedule?: Date;
}

// API Endpoints Types
export type ApiEndpoint =
    | "/api/v1/content/ready"
    | "/api/v1/content/scan"
    | "/api/v1/integrations"
    | "/api/v1/automation/rules"
    | "/api/v1/profiles"
    | "/api/v1/analytics";

// State Types
export interface AppState {
    user: User | null;
    loading: boolean;
    error: string | null;
}

export interface ContentState {
    items: ContentItem[];
    loading: boolean;
    error: string | null;
    filters: {
        status?: ContentItem["status"];
        search?: string;
    };
}

// --- SYSTEM STATUS TYPES (Synced with backend/core/status_manager.py) ---

export type SystemState = 'idle' | 'busy' | 'error' | 'paused' | 'unknown';

export interface JobStatus {
    name: string | null;
    progress: number;
    step: string;
    logs: string[];
}

export interface SystemStats {
    cpu_percent: number;
    ram_percent: number;
    disk_usage: number;
}

export interface BackendStatus {
    state: SystemState;
    last_updated: string;
    timestamp?: number;
    job: JobStatus;
    system?: SystemStats;
    bots?: BotStatus[];
}

export interface BotStatus {
    id: string;
    name: string;
    role: 'UPLOADER' | 'FACTORY' | 'MONITOR' | 'SCHEDULER';
    status: 'online' | 'offline' | 'error' | 'sleeping';
    current_task?: string;
    uptime?: string;
}

// --- PROFILE TYPES (Synced with backend/core/session_manager.py) ---

export interface TikTokProfile {
    id: string;
    label: string;
    username?: string;
    avatar_url?: string;
    icon?: string;
    status: 'active' | 'inactive' | 'expired';
    session_valid?: boolean;
}

// --- WEBSOCKET TYPES ---

export type WebSocketMessageType = 'pipeline_update' | 'log_entry' | 'profile_change' | 'ping' | 'connected' | 'error';

export interface WebSocketPayload<T = unknown> {
    type: WebSocketMessageType;
    data: T;
}

export interface ScheduleEvent {
    id: string;
    profile_id: string;
    video_path: string;
    scheduled_time: string;
    status: 'pending' | 'posted' | 'failed';
    viral_music_enabled?: boolean;
    music_volume?: number;
    trend_category?: string;
}

export interface LogEntry {
    id: string;
    timestamp: string;
    level: 'info' | 'success' | 'warning' | 'error';
    message: string;
    source: string;
}
