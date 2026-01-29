import type { Meta, StoryObj } from '@storybook/react';
import { BatchSidebar } from '../app/components/batch/BatchSidebar';
import { BatchContext } from '../app/components/batch/BatchContext';
// Mock fn
const fn = () => { };

// Mock Profiles
const MOCK_PROFILES = [
    { id: '1', label: 'Atlas Hunter', username: '@atlas_hunter', avatar_url: 'https://i.pravatar.cc/150?u=1' },
    { id: '2', label: 'Forge Writer', username: '@forge_writer', avatar_url: 'https://i.pravatar.cc/150?u=2' },
    { id: '3', label: 'Watcher Eye', username: '@watcher_eye', avatar_url: '' },
];

const DEFAULT_CONTEXT = {
    files: [],
    setFiles: fn,
    selectedProfiles: ['1'],
    setSelectedProfiles: fn,
    profiles: MOCK_PROFILES,
    startDate: '2024-01-01',
    setStartDate: fn,
    startTime: '10:00',
    setStartTime: fn,
    strategy: 'INTERVAL',
    setStrategy: fn,
    intervalMinutes: 60,
    setIntervalMinutes: fn,
    viralBoost: false,
    setViralBoost: fn,
    mixViralSounds: false,
    setMixViralSounds: fn,
    aiCaptions: true,
    handleUpload: fn,
    isValidating: false,
    isUploading: false,
    validationResult: null,
    editingFileId: null,
    setEditingFileId: fn,
    updateFileMetadata: fn,
} as any;

const meta = {
    title: 'Organisms/Batch/BatchSidebar',
    component: BatchSidebar,
    decorators: [
        (Story) => (
            <div className="h-[600px] flex bg-[#0c0c0c]">
                <Story />
            </div>
        ),
    ],
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
} satisfies Meta<typeof BatchSidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};

export const NoneSelected: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT, selectedProfiles: [] }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};

export const AllSelected: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT, selectedProfiles: ['1', '2', '3'] }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};
