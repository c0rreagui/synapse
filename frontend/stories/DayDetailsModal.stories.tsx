import type { Meta, StoryObj } from '@storybook/nextjs';
import DayDetailsModal from '../app/components/DayDetailsModal';
import { TikTokProfile, ScheduleEvent } from '../app/types';
import { useState } from 'react';
import { Button } from '../stories/Button'; // Assuming we have a Button story or just use HTML button for trigger

const meta: Meta<typeof DayDetailsModal> = {
    title: 'App/Organisms/DayDetailsModal',
    component: DayDetailsModal,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof DayDetailsModal>;

const mockProfiles: TikTokProfile[] = [
    { id: 'p1', label: 'Main Account', username: 'synapse_official', avatar_url: '', status: 'active' },
    { id: 'p2', label: 'Backup', username: 'synapse_backup', avatar_url: '', status: 'active' },
];

const mockEvents: ScheduleEvent[] = [
    {
        id: 'e1',
        profile_id: 'p1',
        scheduled_time: new Date().toISOString(),
        video_path: '/videos/viral_clip_1.mp4',
        status: 'pending',
        viral_music_enabled: true
    },
    {
        id: 'e2',
        profile_id: 'p2',
        scheduled_time: new Date(Date.now() + 3600000).toISOString(), // +1 hour
        video_path: '/videos/meme_compilation.mp4',
        status: 'posted',
        viral_music_enabled: false
    }
];

export const Interactive = {
    render: () => {
        const [isOpen, setIsOpen] = useState(false);
        const [events, setEvents] = useState(mockEvents);

        return (
            <div className="h-screen flex items-center justify-center p-8 bg-[#050505]">
                <button
                    onClick={() => setIsOpen(true)}
                    className="px-6 py-3 bg-synapse-purple text-white rounded-lg font-bold hover:bg-synapse-purple/80 transition"
                >
                    Open Day Details
                </button>

                <DayDetailsModal
                    isOpen={isOpen}
                    onClose={() => setIsOpen(false)}
                    date={new Date()}
                    events={events}
                    profiles={mockProfiles}
                    onAddEvent={() => console.log('Add event clicked')}
                    onEditEvent={(id, newTime) => {
                        console.log('Edit event', id, newTime);
                        setEvents(prev => prev.map(e =>
                            e.id === id ? { ...e, scheduled_time: new Date().setHours(parseInt(newTime.split(':')[0]), parseInt(newTime.split(':')[1])).toString() } : e
                        ));
                    }}
                    onDeleteEvent={(id) => {
                        console.log('Delete event', id);
                        setEvents(prev => prev.filter(e => e.id !== id));
                    }}
                />
            </div>
        );
    }
};

export const EmptyState: Story = {
    args: {
        isOpen: true,
        date: new Date(),
        events: [],
        profiles: mockProfiles,
        onClose: () => { },
    },
    decorators: [(Story) => <div className="h-[600px]"><Story /></div>]
};
