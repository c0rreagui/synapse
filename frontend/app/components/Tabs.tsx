'use client';

import { useState, ReactNode } from 'react';

interface Tab {
    id: string;
    label: string;
    icon?: ReactNode;
    badge?: string | number;
    content: ReactNode;
}

interface TabsProps {
    tabs: Tab[];
    defaultTab?: string;
    onChange?: (tabId: string) => void;
}

export default function Tabs({ tabs, defaultTab, onChange }: TabsProps) {
    const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

    const handleTabChange = (tabId: string) => {
        setActiveTab(tabId);
        onChange?.(tabId);
    };

    return (
        <div>
            {/* Tab Headers */}
            <div style={{
                display: 'flex',
                gap: '4px',
                borderBottom: '1px solid var(--cmd-border)',
                marginBottom: '20px',
            }}>
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => handleTabChange(tab.id)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '12px 16px',
                            fontSize: '14px',
                            fontWeight: activeTab === tab.id ? 600 : 400,
                            color: activeTab === tab.id ? 'var(--cmd-text)' : 'var(--cmd-text-muted)',
                            backgroundColor: 'transparent',
                            border: 'none',
                            borderBottom: activeTab === tab.id ? '2px solid var(--cmd-blue)' : '2px solid transparent',
                            marginBottom: '-1px',
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                        }}
                        onMouseEnter={(e) => {
                            if (activeTab !== tab.id) {
                                e.currentTarget.style.color = 'var(--cmd-text)';
                            }
                        }}
                        onMouseLeave={(e) => {
                            if (activeTab !== tab.id) {
                                e.currentTarget.style.color = 'var(--cmd-text-muted)';
                            }
                        }}
                    >
                        {tab.icon}
                        {tab.label}
                        {tab.badge !== undefined && (
                            <span style={{
                                padding: '2px 6px',
                                fontSize: '10px',
                                fontWeight: 600,
                                color: 'var(--cmd-text-muted)',
                                backgroundColor: 'var(--cmd-surface)',
                                borderRadius: '10px',
                            }}>
                                {tab.badge}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div>
                {tabs.find(t => t.id === activeTab)?.content}
            </div>
        </div>
    );
}
