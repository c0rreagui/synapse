import type { Meta, StoryObj } from '@storybook/nextjs';
import DataTable from '../app/components/DataTable';
import Badge from '../app/components/Badge';

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

const DATA = [
    { id: '1', name: 'Video_001.mp4', size: '120MB', status: 'Uploaded', date: '2023-10-01' },
    { id: '2', name: 'Video_002.mp4', size: '450MB', status: 'Processing', date: '2023-10-02' },
    { id: '3', name: 'Short_Clip.mov', size: '12MB', status: 'Error', date: '2023-10-03' },
    { id: '4', name: 'Intro.mp4', size: '55MB', status: 'Uploaded', date: '2023-10-04' },
    { id: '5', name: 'Outro.mp4', size: '30MB', status: 'Uploaded', date: '2023-10-05' },
    { id: '6', name: 'Raw_Footage.mkv', size: '2.4GB', status: 'Pending', date: '2023-10-06' },
];

const COLUMNS = [
    { key: 'name', header: 'File Name', sortable: true },
    { key: 'size', header: 'Size', sortable: true },
    {
        key: 'status',
        header: 'Status',
        sortable: true,
        render: (val: string) => {
            const color = val === 'Uploaded' ? '#3fb950' : val === 'Error' ? '#f85149' : val === 'Processing' ? '#e3b341' : '#8b949e';
            return <span style={{ color, fontWeight: 600 }}>{val}</span>;
        }
    },
    { key: 'date', header: 'Date', sortable: true },
];

export const Default: Story = {
    args: {
        columns: COLUMNS as any,
        data: DATA,
        searchable: true,
        exportable: true,
    },
};

export const Empty: Story = {
    args: {
        columns: COLUMNS as any,
        data: [],
        emptyMessage: 'No files found in the archive.',
    },
};
