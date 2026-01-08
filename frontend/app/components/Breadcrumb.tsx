'use client';

import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

interface BreadcrumbItem {
    label: string;
    href?: string;
    icon?: React.ReactNode;
}

interface BreadcrumbProps {
    items: BreadcrumbItem[];
    showHome?: boolean;
}

export default function Breadcrumb({ items, showHome = true }: BreadcrumbProps) {
    const allItems = showHome
        ? [{ label: 'Home', href: '/', icon: <HomeIcon style={{ width: '14px', height: '14px' }} /> }, ...items]
        : items;

    return (
        <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {allItems.map((item, index) => {
                const isLast = index === allItems.length - 1;

                return (
                    <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {item.href && !isLast ? (
                            <Link
                                href={item.href}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                    color: 'var(--cmd-text-muted)',
                                    fontSize: '13px',
                                    textDecoration: 'none',
                                    transition: 'color 0.15s',
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--cmd-blue)'}
                                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--cmd-text-muted)'}
                            >
                                {item.icon}
                                {item.label}
                            </Link>
                        ) : (
                            <span style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                                color: isLast ? 'var(--cmd-text)' : 'var(--cmd-text-muted)',
                                fontSize: '13px',
                                fontWeight: isLast ? 500 : 400,
                            }}>
                                {item.icon}
                                {item.label}
                            </span>
                        )}

                        {!isLast && (
                            <ChevronRightIcon style={{ width: '12px', height: '12px', color: 'var(--cmd-text-faint)' }} />
                        )}
                    </div>
                );
            })}
        </nav>
    );
}
