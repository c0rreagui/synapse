import type { Meta, StoryObj } from '@storybook/react';
import { BatchMain } from '../app/components/batch/BatchMain';
import { BatchContext } from '../app/components/batch/BatchContext';
// Mock fn
const fn = () => { };

// Mock Files
const MOCK_FILE_1 = {
    file: new File([""], "video1.mp4"),
    preview: '',
    duration: 120,
    status: 'pending',
    progress: 0,
    id: 'f1',
    metadata: { caption: "Awesome video!" }
};

const MOCK_FILE_2 = {
    file: new File([""], "viral_clip.mov"),
    preview: '',
    duration: 15,
    status: 'uploading',
    progress: 45,
    id: 'f2',
    metadata: { caption: "Wait for it..." }
};

const DEFAULT_CONTEXT = {
    files: [],
    setFiles: fn,
    selectedProfiles: [],
    setSelectedProfiles: fn,
    profiles: [],
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
    title: 'Organisms/Batch/BatchMain',
    component: BatchMain,
    decorators: [
        (Story) => (
            <div className="h-[600px] flex bg-[#0c0c0c]">
                <Story />
            </div>
        ),
    ],
    parameters: {
        layout: 'fullscreen',
    },
    tags: ['autodocs'],
} satisfies Meta<typeof BatchMain>;

export default meta;
type Story = StoryObj<typeof meta>;

export const EmptyState: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};

export const WithFiles: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT, files: [MOCK_FILE_1, MOCK_FILE_2] }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};

export const ViralBoostEnabled: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{ ...DEFAULT_CONTEXT, viralBoost: true, mixViralSounds: true }}>
                <Story />
            </BatchContext.Provider>
        ),
    ],
};
