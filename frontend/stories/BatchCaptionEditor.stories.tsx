import type { Meta, StoryObj } from '@storybook/nextjs';
import { BatchCaptionEditor } from '../app/components/batch/BatchCaptionEditor';
import { BatchContext } from '../app/components/batch/BatchContext';

// Mock File object
const mockFile = new File(["foo"], "viral_dance.mp4", { type: "video/mp4" });
const mockFileUpload = {
    file: mockFile,
    preview: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4', // Valid sample video
    duration: 15,
    status: 'pending' as const,
    progress: 0,
    id: '123',
    metadata: {
        caption: 'This is a generated caption example. #viral #fyp',
        aiRequest: {
            prompt: 'Make it funny',
            tone: 'Engraçado',
            hashtags: true
        }
    }
};

const meta: Meta<typeof BatchCaptionEditor> = {
    title: 'App/Features/Batch/BatchCaptionEditor',
    component: BatchCaptionEditor,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="h-screen w-full relative bg-gray-900">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof BatchCaptionEditor>;

export const Default: Story = {
    decorators: [
        (Story) => (
            <BatchContext.Provider value={{
                files: [mockFileUpload],
                setFiles: () => { },
                selectedProfiles: [],
                setSelectedProfiles: () => { },
                profiles: [],
                startDate: '',
                setStartDate: () => { },
                startTime: '',
                setStartTime: () => { },
                strategy: 'INTERVAL',
                setStrategy: () => { },
                intervalMinutes: 60,
                setIntervalMinutes: () => { },
                viralBoost: false,
                setViralBoost: () => { },
                mixViralSounds: false,
                setMixViralSounds: () => { },
                aiCaptions: true,
                handleUpload: async () => { },
                isValidating: false,
                isUploading: false,
                validationResult: null,
                editingFileId: '123', // Active ID matches mock file
                setEditingFileId: () => { },
                updateFileMetadata: () => { }
            } as any}>
                <Story />
            </BatchContext.Provider>
        )
    ]
};
