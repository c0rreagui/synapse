"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        };
    }

    static getDerivedStateFromError(_: Error): Partial<State> {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        // Log error to error reporting service
        console.error("ErrorBoundary caught an error:", error, errorInfo);

        this.setState({
            error,
            errorInfo,
        });

        // TODO: Send to error tracking service (Sentry, etc.)
        // logErrorToService(error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="min-h-screen flex items-center justify-center bg-background p-6">
                    <div className="glass-panel rounded-2xl p-8 max-w-2xl w-full">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="size-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                                <span className="material-symbols-outlined text-red-500 text-2xl">warning</span>
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white font-display">Oops! Algo deu errado</h2>
                                <p className="text-sm text-gray-400">Encontramos um problema inesperado</p>
                            </div>
                        </div>

                        {process.env.NODE_ENV === "development" && this.state.error && (
                            <details className="mt-6">
                                <summary className="cursor-pointer text-sm text-gray-400 hover:text-white font-mono mb-2">
                                    Detalhes técnicos (dev only)
                                </summary>
                                <div className="bg-black/40 rounded-lg p-4 border border-white/5 overflow-auto">
                                    <pre className="text-xs text-red-400 font-mono">
                                        {this.state.error.toString()}
                                        {"\n\n"}
                                        {this.state.errorInfo?.componentStack}
                                    </pre>
                                </div>
                            </details>
                        )}

                        <div className="flex gap-4 mt-8">
                            <button
                                onClick={() => window.location.reload()}
                                className="flex-1 bg-primary hover:bg-primary/80 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                            >
                                Recarregar Página
                            </button>
                            <button
                                onClick={() => window.location.href = "/"}
                                className="flex-1 bg-white/5 hover:bg-white/10 text-white font-bold py-3 px-6 rounded-lg border border-white/10 transition-colors"
                            >
                                Ir para Home
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
