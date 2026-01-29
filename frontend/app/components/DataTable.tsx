'use client';

import { useState, ReactNode } from 'react';
import { ChevronUp, ChevronDown, Search, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';
import { NeoButton } from '../../components/design-system/NeoButton';

interface Column<T> {
    key: keyof T;
    header: string;
    sortable?: boolean;
    render?: (value: T[keyof T], row: T) => ReactNode;
    width?: string;
    align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
    columns: Column<T>[];
    data: T[];
    searchable?: boolean;
    exportable?: boolean;
    onRowClick?: (row: T) => void;
    emptyMessage?: string;
    rowsPerPage?: number;
}

export default function DataTable<T extends { id: string }>({
    columns,
    data,
    searchable = true,
    exportable = true,
    onRowClick,
    emptyMessage = 'Nenhum dado encontrado',
    rowsPerPage = 10,
}: DataTableProps<T>) {
    const [sortKey, setSortKey] = useState<keyof T | null>(null);
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [currentPage, setCurrentPage] = useState(1);

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

    // Pagination
    const totalPages = Math.ceil(sortedData.length / rowsPerPage);
    const paginatedData = sortedData.slice(
        (currentPage - 1) * rowsPerPage,
        currentPage * rowsPerPage
    );

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
        if (selectedIds.size === paginatedData.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(paginatedData.map(r => r.id)));
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
        <div className="w-full flex flex-col gap-4">
            {/* Toolbar */}
            <div className="flex items-center gap-4">
                {searchable && (
                    <div className="flex items-center gap-3 px-4 py-2 bg-white/5 border border-white/10 rounded-xl focus-within:border-white/20 focus-within:bg-white/10 transition-all flex-1 max-w-sm">
                        <Search className="w-4 h-4 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Buscar registros..."
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }} // Reset to page 1 on search
                            className="bg-transparent border-none outline-none text-sm text-gray-200 placeholder-gray-500 w-full"
                        />
                    </div>
                )}

                <div className="flex-1" />

                <span className="text-xs text-gray-500 font-mono">
                    {sortedData.length} registro{sortedData.length !== 1 ? 's' : ''}
                    {selectedIds.size > 0 && ` • ${selectedIds.size} selecionado${selectedIds.size > 1 ? 's' : ''}`}
                </span>

                {exportable && (
                    <NeoButton variant="secondary" size="sm" onClick={exportCSV} className="gap-2">
                        <Download className="w-3 h-3" />
                        CSV
                    </NeoButton>
                )}
            </div>

            {/* Table Container */}
            <div className="rounded-2xl border border-white/10 bg-[#0d1117]/50 backdrop-blur-md overflow-hidden relative">
                {/* Glow Effect */}
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-synapse-purple/50 to-transparent opacity-50" />

                <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                        <thead>
                            <tr className="bg-white/5 border-b border-white/10">
                                <th className="p-4 w-12 text-center text-gray-400">
                                    <input
                                        type="checkbox"
                                        checked={selectedIds.size === paginatedData.length && paginatedData.length > 0}
                                        onChange={toggleSelectAll}
                                        className="rounded border-gray-600 bg-transparent text-synapse-purple focus:ring-0 focus:ring-offset-0 w-4 h-4 cursor-pointer accent-synapse-purple"
                                    />
                                </th>
                                {columns.map(col => (
                                    <th
                                        key={String(col.key)}
                                        onClick={() => col.sortable && handleSort(col.key)}
                                        className={clsx(
                                            "p-4 text-xs font-bold text-gray-400 uppercase tracking-wider select-none transition-colors",
                                            col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
                                            col.sortable && "cursor-pointer hover:text-white group"
                                        )}
                                        style={{ width: col.width }}
                                    >
                                        <div className={clsx(
                                            "flex items-center gap-1",
                                            col.align === 'center' && "justify-center",
                                            col.align === 'right' && "justify-end"
                                        )}>
                                            {col.header}
                                            {col.sortable && (
                                                <div className="flex flex-col text-gray-600 group-hover:text-synapse-purple transition-colors">
                                                    {sortKey === col.key ? (
                                                        sortDir === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                                                    ) : (
                                                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50"><ChevronDown className="w-3 h-3" /></div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedData.length > 0 ? paginatedData.map((row, i) => (
                                <tr
                                    key={row.id}
                                    onClick={() => onRowClick?.(row)}
                                    className={clsx(
                                        "group border-b border-white/5 transition-all duration-200",
                                        selectedIds.has(row.id) ? "bg-synapse-purple/10" : "hover:bg-white/5",
                                        onRowClick && "cursor-pointer"
                                    )}
                                >
                                    <td className="p-4 text-center">
                                        <input
                                            type="checkbox"
                                            checked={selectedIds.has(row.id)}
                                            onChange={(e) => toggleSelect(row.id, e as unknown as React.MouseEvent)}
                                            className="rounded border-gray-600 bg-transparent text-synapse-purple focus:ring-0 focus:ring-offset-0 w-4 h-4 cursor-pointer accent-synapse-purple opacity-50 group-hover:opacity-100 transition-opacity"
                                        />
                                    </td>
                                    {columns.map(col => (
                                        <td
                                            key={String(col.key)}
                                            className={clsx(
                                                "p-4 text-sm text-gray-300 group-hover:text-white transition-colors",
                                                col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left'
                                            )}
                                        >
                                            {col.render ? col.render(row[col.key], row) : (row[col.key] as ReactNode)}
                                        </td>
                                    ))}
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={columns.length + 1} className="py-12 text-center text-gray-500">
                                        <div className="flex flex-col items-center gap-2">
                                            <Search className="w-8 h-8 opacity-20" />
                                            <p className="text-sm">{emptyMessage}</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between p-4 border-t border-white/10 bg-white/[0.02]">
                        <span className="text-xs text-gray-500">
                            Página {currentPage} de {totalPages}
                        </span>
                        <div className="flex items-center gap-2">
                            <NeoButton
                                variant="ghost"
                                size="icon"
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                                className="w-8 h-8"
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </NeoButton>
                            <NeoButton
                                variant="ghost"
                                size="icon"
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                disabled={currentPage === totalPages}
                                className="w-8 h-8"
                            >
                                <ChevronRight className="w-4 h-4" />
                            </NeoButton>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
