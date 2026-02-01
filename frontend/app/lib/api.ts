// API Error Classes
import { getApiUrl } from "../utils/apiClient";
export class ApiError extends Error {
    constructor(
        message: string,
        public statusCode: number,
        public endpoint: string,
        public data?: unknown
    ) {
        super(message);
        this.name = "ApiError";
    }
}

export class NetworkError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "NetworkError";
    }
}

export class ValidationError extends Error {
    constructor(message: string, public fields?: Record<string, string>) {
        super(message);
        this.name = "ValidationError";
    }
}

// API Response Types
export interface ApiResponse<T> {
    data: T;
    status: "success" | "error";
    message?: string;
}

export interface ApiErrorResponse {
    error: string;
    message: string;
    statusCode: number;
    details?: unknown;
}

// API Client Configurator
class ApiClient {
    private baseURL: string;
    private defaultHeaders: HeadersInit;

    constructor(baseURL: string) {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            "Content-Type": "application/json",
        };
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new ApiError(
                errorData.message || "API request failed",
                response.status,
                response.url,
                errorData
            );
        }

        const data = await response.json();
        return data as T;
    }

    async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: "GET",
                headers: { ...this.defaultHeaders, ...options?.headers },
                ...options,
            });

            return await this.handleResponse<T>(response);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new NetworkError(`Network error during GET ${endpoint}: ${error}`);
        }
    }

    async post<T, D = unknown>(
        endpoint: string,
        data?: D,
        options?: RequestInit
    ): Promise<T> {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: "POST",
                headers: { ...this.defaultHeaders, ...options?.headers },
                body: data ? JSON.stringify(data) : undefined,
                ...options,
            });

            return await this.handleResponse<T>(response);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new NetworkError(`Network error during POST ${endpoint}: ${error}`);
        }
    }

    async put<T, D = unknown>(
        endpoint: string,
        data?: D,
        options?: RequestInit
    ): Promise<T> {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: "PUT",
                headers: { ...this.defaultHeaders, ...options?.headers },
                body: data ? JSON.stringify(data) : undefined,
                ...options,
            });

            return await this.handleResponse<T>(response);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new NetworkError(`Network error during PUT ${endpoint}: ${error}`);
        }
    }

    async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: "DELETE",
                headers: { ...this.defaultHeaders, ...options?.headers },
                ...options,
            });

            return await this.handleResponse<T>(response);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new NetworkError(`Network error during DELETE ${endpoint}: ${error}`);
        }
    }
}

// Create singleton instance
export const apiClient = new ApiClient(
    getApiUrl()
);

// Error Handler Utility
export function handleApiError(error: unknown): string {
    if (error instanceof ApiError) {
        return error.message;
    }

    if (error instanceof NetworkError) {
        return "Erro de conexão. Verifique sua internet e tente novamente.";
    }

    if (error instanceof ValidationError) {
        return error.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    return "Ocorreu um erro inesperado. Tente novamente.";
}

// Retry utility with exponential backoff
export async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
): Promise<T> {
    let lastError: unknown;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;

            // Don't retry on validation errors or 4xx errors (except 429)
            if (error instanceof ApiError) {
                if (error.statusCode >= 400 && error.statusCode < 500 && error.statusCode !== 429) {
                    throw error;
                }
            }

            if (attempt < maxRetries - 1) {
                const delay = baseDelay * Math.pow(2, attempt);
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    }

    throw lastError;
}

// Logger utility
export const logger = {
    info: (message: string, data?: unknown) => {
        if (process.env.NODE_ENV !== "production") {
            console.log(`[INFO] ${message}`, data);
        }
    },

    warn: (message: string, data?: unknown) => {
        console.warn(`[WARN] ${message}`, data);
    },

    error: (message: string, error?: unknown) => {
        console.error(`[ERROR] ${message}`, error);
        // TODO: Send to error tracking service
    },

    debug: (message: string, data?: unknown) => {
        if (process.env.NODE_ENV === "development") {
            console.debug(`[DEBUG] ${message}`, data);
        }
    },
};
