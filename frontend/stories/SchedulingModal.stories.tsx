import type { Meta, StoryObj } from '@storybook/nextjs';
import SchedulingModal from '../app/components/SchedulingModal';
import { TikTokProfile } from '../app/types';
import { useState } from 'react';

const mockProfiles: TikTokProfile[] = [
    { id: 'p1', label: 'Main Account', username: 'synapse_official', avatar_url: '' },
    { id: 'p2', label: 'Backup', username: 'synapse_backup', avatar_url: '' },
    { id: 'p3', label: 'Test Channel', username: 'synapse_test', avatar_url: '' },
];

const meta: Meta<typeof SchedulingModal> = {
    title: 'App/Organisms/SchedulingModal',
    component: SchedulingModal,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof SchedulingModal>;

export const Interactive = {
    render: () => {
        const [isOpen, setIsOpen] = useState(true);

        return (
            <div className="h-screen w-full bg-[#050505] flex items-center justify-center">
                <button
                    onClick={() => setIsOpen(true)}
                    className="px-6 py-3 bg-synapse-purple text-white rounded-lg font-bold hover:bg-synapse-purple/80 transition"
                >
                    Open Scheduler
                </button>

                <SchedulingModal
                    isOpen={isOpen}
                    onClose={() => setIsOpen(false)}
                    onSubmit={(data) => {
                        console.log('Scheduled Data:', data);
                        alert(`Scheduled for ${data.scheduled_time}`);
                    }}
                    initialDate={new Date()}
                    profiles={mockProfiles}
                />
            </div>
        );
    }
};

export const ViralBoostActivated: Story = {
    args: {
        isOpen: true,
        initialDate: new Date(),
        profiles: mockProfiles,
        initialViralBoost: true,
        onClose: () => { },
        onSubmit: () => { },
    },
    decorators: [(Story) => <div className="h-[800px] flex items-center justify-center"><Story /></div>]
};
