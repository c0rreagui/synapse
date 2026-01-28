import type { Meta, StoryObj } from '@storybook/nextjs';
import ConfirmDialog from '../app/components/ConfirmDialog';
import { useState } from 'react';
import { NeonButton } from '../app/components/NeonButton';

const meta: Meta<typeof ConfirmDialog> = {
    title: 'App/Molecules/ConfirmDialog',
    component: ConfirmDialog,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
        docs: {
            story: {
                inline: false,
                iframeHeight: 400,
            },
        },
    },
};

export default meta;
type Story = StoryObj<typeof ConfirmDialog>;

export const Interactive = {
    render: () => {
        const [isOpen, setIsOpen] = useState(false);
        return (
            <div>
                <NeonButton onClick={() => setIsOpen(true)}>Open Dialog</NeonButton>
                <ConfirmDialog
                    isOpen={isOpen}
                    title="Delete Project?"
                    message="This action cannot be undone. All data will be lost."
                    onConfirm={() => { alert('Confirmed!'); setIsOpen(false); }}
                    onCancel={() => setIsOpen(false)}
                    variant="danger"
                    confirmLabel="Delete Forever"
                />
            </div>
        );
    }
};

export const Warning: Story = {
    args: {
        isOpen: true,
        title: 'Unsaved Changes',
        message: 'You have unsaved changes. Are you sure you want to leave?',
        variant: 'warning',
        confirmLabel: 'Leave Anyway',
    },
    decorators: [(Story) => <div className="h-64"><Story /></div>],
};

export const Info: Story = {
    args: {
        isOpen: true,
        title: 'Update Available',
        message: 'A new version of the app is available.',
        variant: 'info',
        confirmLabel: 'Update Now',
    },
    decorators: [(Story) => <div className="h-64"><Story /></div>],
};
