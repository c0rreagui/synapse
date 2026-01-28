import type { Meta, StoryObj } from '@storybook/nextjs';
import UndoToast from '../app/components/UndoToast';
import { useState } from 'react';
import { NeonButton } from '../app/components/NeonButton';

const meta: Meta<typeof UndoToast> = {
    title: 'App/Molecules/UndoToast',
    component: UndoToast,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof UndoToast>;

export const Interactive = {
    render: () => {
        const [show, setShow] = useState(false);
        const [lastAction, setLastAction] = useState('None');

        const trigger = () => {
            setShow(false);
            setTimeout(() => setShow(true), 100);
            setLastAction('Deleted Item');
        };

        return (
            <div className="h-64 relative flex flex-col items-center justify-center gap-4">
                <div className="text-white mb-4">Last Action: {lastAction}</div>
                <NeonButton onClick={trigger}>Delete Something</NeonButton>

                {show && (
                    <UndoToast
                        message="Item moved to trash."
                        duration={5000}
                        onUndo={() => { alert('Indo Triggered'); setShow(false); setLastAction('Undone'); }}
                        onClose={() => setShow(false)}
                        onTimeout={() => { console.log('Timeout'); setShow(false); }}
                    />
                )}
            </div>
        );
    }
};

export const PermanentDisplay: Story = {
    args: {
        message: 'This is a static preview of the toast.',
        duration: 999999, // Long duration for static view
        onUndo: () => { },
        onClose: () => { },
        onTimeout: () => { },
    },
    decorators: [
        (Story) => (
            <div className="h-32 transform translate-x-12 translate-y-[-50px]">
                <Story />
            </div>
        )
    ]
};
