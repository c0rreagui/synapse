import type { Meta, StoryObj } from '@storybook/nextjs';
import BatchUploadModal from '../app/components/BatchUploadModal';
import { TikTokProfile } from '../app/types';
import { useState } from 'react';

const mockProfiles: TikTokProfile[] = [
    { id: 'p1', label: 'Main Account', username: 'synapse_official', avatar_url: '', status: 'active' },
    { id: 'p2', label: 'Backup', username: 'synapse_backup', avatar_url: '', status: 'active' },
    { id: 'p3', label: 'Test Channel', username: 'synapse_test', avatar_url: '', status: 'inactive' },
];

const meta: Meta<typeof BatchUploadModal> = {
    title: 'App/Organisms/BatchUploadModal',
    component: BatchUploadModal,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof BatchUploadModal>;

export const Interactive = {
    render: () => {
        const [isOpen, setIsOpen] = useState(true);

        return (
            <div className="h-screen w-full bg-[#050505] flex items-center justify-center">
                <button
                    onClick={() => setIsOpen(true)}
                    className="px-6 py-3 bg-synapse-purple text-white rounded-lg font-bold hover:bg-synapse-purple/80 transition"
                >
                    Abrir Batch Upload
                </button>

                <BatchUploadModal
                    isOpen={isOpen}
                    onClose={() => setIsOpen(false)}
                    onSuccess={() => {
                        alert('Batch concluído com sucesso!');
                        setIsOpen(false);
                    }}
                    profiles={mockProfiles}
                />
            </div>
        );
    }
};

export const OpenState: Story = {
    args: {
        isOpen: true,
        profiles: mockProfiles,
        onClose: () => { },
        onSuccess: () => { },
    },
    decorators: [(Story) => <div className="h-[900px] flex items-center justify-center"><Story /></div>]
};
