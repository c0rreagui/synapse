import type { Meta, StoryObj } from '@storybook/nextjs';
import FileListItem from '../app/components/FileListItem';

const meta: Meta<typeof FileListItem> = {
    title: 'App/Molecules/FileListItem',
    component: FileListItem,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-full max-w-2xl mx-auto">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof FileListItem>;

export const Ready: Story = {
    args: {
        filename: 'awesome_dance_video.mp4',
        status: 'ready',
        resolution: '1080p',
        duration: '00:15',
        size: '12.5 MB',
    },
};

export const Processing: Story = {
    args: {
        filename: 'heavy_compilation.mov',
        status: 'processing',
        progress: 45,
    },
};

export const Uploading: Story = {
    args: {
        filename: 'new_upload.mp4',
        status: 'uploading',
        progress: 78,
    },
};

export const Queued: Story = {
    args: {
        filename: 'scheduled_post.mp4',
        status: 'queued',
        duration: '01:00',
    },
};
