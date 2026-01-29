import type { Meta, StoryObj } from '@storybook/react';
import { BatchFooter } from '../app/components/batch/BatchFooter';
import { BatchContext } from '../app/components/batch/BatchContext';
// Mock fn
const fn = () => { };

// Mock Profiles
const MOCK_PROFILES = [
    { id: '1', label: 'Atlas Hunter', username: '@atlas_hunter', avatar_url: 'https://i.pravatar.cc/150?u=1' },
    { id: '2', label: 'Forge Writer', username: '@forge_writer', avatar_url: 'https://i.pravatar.cc/150?u=2' },
];

const DEFAULT_CONTEXT = {
    files: [new File([""], "video.mp4")],
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
    title: 'Organisms/Batch/BatchFooter',
    component: BatchFooter,
    decorators: [
        (Story) => (
            <div className="h-40 relative bg-black">
                <Story />
            </div>
        ),
    ],
    parameters: {
        layout: 'fullscreen',
    },
    tags: ['autodocs'],
    args: {
        onClose: fn,
    },
} satisfies Meta<typeof BatchFooter>;

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

export const StrategyOracle: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT, strategy: 'ORACLE' }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};

export const Validating: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT, isValidating: true }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};

export const WithConflicts: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{
                ...DEFAULT_CONTEXT,
                validationResult: {
                    issues: [{ severity: 'error', message: 'Slot occupied' }, { severity: 'error', message: 'Rate limit' }]
                }
            }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};
