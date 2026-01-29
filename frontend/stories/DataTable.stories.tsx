import type { Meta, StoryObj } from '@storybook/nextjs';
import DataTable from '../app/components/DataTable';

const meta: Meta<typeof DataTable> = {
    title: 'App/Organisms/DataTable',
    component: DataTable,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof DataTable>;

const DATA = Array.from({ length: 25 }, (_, i) => ({
    id: String(i + 1),
    name: `Video_${String(i + 1).padStart(3, '0')}.mp4`,
    size: `${Math.floor(Math.random() * 500 + 10)}MB`,
    status: i % 5 === 0 ? 'Error' : i % 3 === 0 ? 'Processing' : 'Uploaded',
    date: `2023-10-${String(i % 30 + 1).padStart(2, '0')}`,
}));

const COLUMNS = [
    { key: 'name', header: 'File Name', sortable: true, width: '30%' },
    { key: 'size', header: 'Size', sortable: true, align: 'right', width: '15%' },
    {
        key: 'status',
        header: 'Status',
        sortable: true,
        align: 'center',
        render: (val: string) => {
            const color = val === 'Uploaded' ? 'text-emerald-400' : val === 'Error' ? 'text-red-400' : 'text-amber-400';
            return <span className={`font-semibold ${color}`}>{val}</span>;
        }
    },
    { key: 'date', header: 'Date', sortable: true, align: 'right' },
];

export const Default: Story = {
    args: {
        columns: COLUMNS as any,
        data: DATA.slice(0, 5), // Small dataset
        searchable: true,
        exportable: true,
        rowsPerPage: 5,
    },
};

export const Paginated: Story = {
    args: {
        columns: COLUMNS as any,
        data: DATA, // 25 items
        searchable: true,
        exportable: true,
        rowsPerPage: 5,
    },
};

export const Empty: Story = {
    args: {
        columns: COLUMNS as any,
        data: [],
        emptyMessage: 'No files found in the archive.',
    },
};
