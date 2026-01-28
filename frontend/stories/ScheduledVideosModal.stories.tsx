import type { Meta, StoryObj } from '@storybook/nextjs';
import ScheduledVideosModal from '../app/components/ScheduledVideosModal';
import { TikTokProfile } from '../app/types';
import { useState } from 'react';

const mockProfiles: TikTokProfile[] = [
    { id: '1', label: 'Synapse Main', username: 'synapse_official', avatar_url: '', status: 'active' },
    { id: '2', label: 'Backup Account', username: 'synapse_v2', avatar_url: '', status: 'active' }
];

const mockEvents = [
    {
        id: 'evt1',
        video_path: '/videos/viral_clip_v1.mp4',
        scheduled_time: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
        profile_id: '1',
        status: 'pending',
        viral_music_enabled: true
    },
    {
        id: 'evt2',
        video_path: '/videos/funny_cat.mov',
        scheduled_time: new Date(Date.now() + 172800000).toISOString(), // Day after tomorrow
        profile_id: '2',
        status: 'pending',
        viral_music_enabled: false
    }
];

// Mock Fetch Global
const mockFetch = (url: string, options?: any): Promise<any> => {
    return new Promise((resolve) => {
        if (url.includes('/scheduler/list')) {
            resolve({
                ok: true,
                json: async () => mockEvents
            });
            return;
        }
        if (url.includes('/scheduler/') && options?.method === 'DELETE') {
            resolve({ ok: true });
            return;
        }
        resolve({ ok: false });
    });
};

const meta: Meta<typeof ScheduledVideosModal> = {
    title: 'App/Organisms/ScheduledVideosModal',
    component: ScheduledVideosModal,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => {
            // @ts-ignore
            global.fetch = mockFetch;
            return (
                <div className="h-screen w-full flex items-center justify-center bg-gray-900 p-8">
                    <Story />
                </div>
            )
        },
    ],
};

export default meta;
type Story = StoryObj<typeof ScheduledVideosModal>;

export const Default: Story = {
    render: () => {
        const [isOpen, setIsOpen] = useState(true);
        return (
            <>
                <button
                    onClick={() => setIsOpen(true)}
                    className="px-4 py-2 bg-purple-600 rounded text-white"
                >
                    Open Scheduled Videos
                </button>
                <ScheduledVideosModal
                    isOpen={isOpen}
                    onClose={() => setIsOpen(false)}
                    profiles={mockProfiles}
                    onDelete={(id) => console.log('Deleted', id)}
                />
            </>
        )
    }
};

export const Empty: Story = {
    decorators: [
        (Story) => {
            // Override mock for empty state
            // @ts-ignore
            global.fetch = () => Promise.resolve({ ok: true, json: async () => [] });
            return <Story />
        }
    ],
    args: {
        isOpen: true,
        onClose: () => { },
        profiles: mockProfiles,
    }
};
