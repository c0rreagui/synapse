'use client';

import { useState, ReactNode } from 'react';
import { ChevronUpIcon, ChevronDownIcon, MagnifyingGlassIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

interface Column<T> {
    key: keyof T;
    header: string;
    sortable?: boolean;
    render?: (value: T[keyof T], row: T) => ReactNode;
    width?: string;
}

interface DataTableProps<T> {
    columns: Column<T>[];
    data: T[];
    searchable?: boolean;
    exportable?: boolean;
    onRowClick?: (row: T) => void;
    emptyMessage?: string;
}

export default function DataTable<T extends { id: string }>({
    columns,
    data,
    searchable = true,
    exportable = true,
    onRowClick,
    emptyMessage = 'Nenhum dado encontrado',
}: DataTableProps<T>) {
    const [sortKey, setSortKey] = useState<keyof T | null>(null);
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    // Filter data
    const filteredData = data.filter(row =>
        Object.values(row).some(val =>
            String(val).toLowerCase().includes(searchQuery.toLowerCase())
        )
    );

    // Sort data
    const sortedData = [...filteredData].sort((a, b) => {
        if (!sortKey) return 0;
        const aVal = String(a[sortKey]);
        const bVal = String(b[sortKey]);
        return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });

    const handleSort = (key: keyof T) => {
        if (sortKey === key) {
            setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortDir('asc');
        }
    };

    const toggleSelect = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const newSet = new Set(selectedIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        setSelectedIds(newSet);
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === sortedData.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(sortedData.map(r => r.id)));
        }
    };

    const exportCSV = () => {
        const headers = columns.map(c => c.header).join(',');
        const rows = sortedData.map(row =>
            columns.map(c => String(row[c.key])).join(',')
        ).join('\n');
        const csv = `${headers}\n${rows}`;
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'export.csv';
        a.click();
    };

    return (
        <div>
            {/* Toolbar */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', alignItems: 'center' }}>
                {searchable && (
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        flex: 1,
                        maxWidth: '300px',
                        padding: '8px 12px',
                        backgroundColor: '#0d1117',
                        border: '1px solid #30363d',
                        borderRadius: '8px',
                    }}>
                        <MagnifyingGlassIcon style={{ width: '16px', height: '16px', color: '#8b949e' }} />
                        <input
                            type="text"
                            placeholder="Buscar..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{
                                flex: 1,
                                background: 'none',
                                border: 'none',
                                outline: 'none',
                                color: '#c9d1d9',
                                fontSize: '13px',
                            }}
                        />
                    </div>
                )}

                <div style={{ flex: 1 }} />

                <span style={{ fontSize: '12px', color: '#8b949e' }}>
                    {sortedData.length} item{sortedData.length !== 1 ? 's' : ''}
                    {selectedIds.size > 0 && ` (${selectedIds.size} selecionado${selectedIds.size > 1 ? 's' : ''})`}
                </span>

                {exportable && (
                    <button
                        onClick={exportCSV}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '8px 12px',
                            backgroundColor: '#21262d',
                            border: '1px solid #30363d',
                            borderRadius: '6px',
                            color: '#c9d1d9',
                            fontSize: '12px',
                            cursor: 'pointer',
                        }}
                    >
                        <ArrowDownTrayIcon style={{ width: '14px', height: '14px' }} />
                        Export CSV
                    </button>
                )}
            </div>

            {/* Table */}
            <div style={{
                borderRadius: '10px',
                border: '1px solid #30363d',
                overflow: 'hidden',
                backgroundColor: '#0d1117',
            }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ backgroundColor: '#161b22' }}>
                            <th style={{ width: '40px', padding: '12px' }}>
                                <input
                                    type="checkbox"
                                    title="Selecionar todos"
                                    aria-label="Selecionar todos os itens"
                                    checked={selectedIds.size === sortedData.length && sortedData.length > 0}
                                    onChange={toggleSelectAll}
                                    style={{ cursor: 'pointer' }}
                                />
                            </th>
                            {columns.map(col => (
                                <th
                                    key={String(col.key)}
                                    onClick={() => col.sortable && handleSort(col.key)}
                                    style={{
                                        padding: '12px 16px',
                                        textAlign: 'left',
                                        fontSize: '12px',
                                        fontWeight: 600,
                                        color: '#8b949e',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.5px',
                                        cursor: col.sortable ? 'pointer' : 'default',
                                        userSelect: 'none',
                                        width: col.width,
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                        {col.header}
                                        {col.sortable && sortKey === col.key && (
                                            sortDir === 'asc'
                                                ? <ChevronUpIcon style={{ width: '14px', height: '14px' }} />
                                                : <ChevronDownIcon style={{ width: '14px', height: '14px' }} />
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {sortedData.length > 0 ? sortedData.map((row, i) => (
                            <tr
                                key={row.id}
                                onClick={() => onRowClick?.(row)}
                                style={{
                                    backgroundColor: selectedIds.has(row.id) ? 'rgba(88,166,255,0.1)' : i % 2 === 0 ? '#0d1117' : '#161b22',
                                    cursor: onRowClick ? 'pointer' : 'default',
                                    transition: 'background-color 0.15s',
                                }}
                            >
                                <td style={{ padding: '12px', textAlign: 'center' }}>
                                    <input
                                        type="checkbox"
                                        title="Selecionar item"
                                        aria-label="Selecionar este item"
                                        checked={selectedIds.has(row.id)}
                                        onChange={(e) => toggleSelect(row.id, e as unknown as React.MouseEvent)}
                                        style={{ cursor: 'pointer' }}
                                    />
                                </td>
                                {columns.map(col => (
                                    <td
                                        key={String(col.key)}
                                        style={{
                                            padding: '12px 16px',
                                            fontSize: '13px',
                                            color: '#c9d1d9',
                                            borderTop: '1px solid #21262d',
                                        }}
                                    >
                                        {col.render ? col.render(row[col.key], row) : String(row[col.key])}
                                    </td>
                                ))}
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan={columns.length + 1} style={{ padding: '40px', textAlign: 'center', color: '#8b949e' }}>
                                    {emptyMessage}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
