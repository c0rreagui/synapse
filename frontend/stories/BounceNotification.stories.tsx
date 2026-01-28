import type { Meta, StoryObj } from '@storybook/nextjs';
import BounceNotification from '../app/components/BounceNotification';
import { useState } from 'react';
import { NeonButton } from '../app/components/NeonButton';

const meta: Meta<typeof BounceNotification> = {
    title: 'App/Molecules/BounceNotification',
    component: BounceNotification,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof BounceNotification>;

export const Interactive = {
    render: () => {
        const [show, setShow] = useState(false);

        return (
            <div className="h-64 flex items-center justify-center">
                <NeonButton onClick={() => setShow(true)}>Show Notification</NeonButton>

                <BounceNotification
                    show={show}
                    onClose={() => setShow(false)}
                    position="bottom-right"
                >
                    <div className="bg-emerald-500 text-black px-4 py-3 rounded-lg font-bold shadow-lg">
                        Achievement Unlocked: Storybook Hero 🏆
                    </div>
                </BounceNotification>
            </div>
        );
    }
};
