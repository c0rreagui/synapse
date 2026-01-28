import type { Meta, StoryObj } from '@storybook/nextjs';
import ShakeOnError from '../app/components/ShakeOnError';
import { useState } from 'react';
import { NeonButton } from '../app/components/NeonButton';

const meta: Meta<typeof ShakeOnError> = {
    title: 'App/Utilities/ShakeOnError',
    component: ShakeOnError,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof ShakeOnError>;

export const Interactive = {
    render: () => {
        const [shake, setShake] = useState(false);

        const triggerError = () => {
            setShake(true);
        };

        return (
            <div className="flex flex-col items-center gap-4">
                <ShakeOnError shake={shake} onAnimationEnd={() => setShake(false)}>
                    <div className="p-4 bg-red-500/10 border border-red-500 text-red-500 rounded-lg">
                        Incorrect Password
                    </div>
                </ShakeOnError>
                <NeonButton onClick={triggerError} variant="danger">
                    Trigger Shake
                </NeonButton>
            </div>
        );
    }
};
