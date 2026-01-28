import type { Meta, StoryObj } from '@storybook/nextjs';
import EstimatedTime from '../app/components/EstimatedTime';
import { useEffect, useState } from 'react';

const meta: Meta<typeof EstimatedTime> = {
    title: 'App/Molecules/EstimatedTime',
    component: EstimatedTime,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof EstimatedTime>;

// Helper to simulate progress for demo
const ProgressSimulation = () => {
    const [completed, setCompleted] = useState(0);
    const [startTime] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            setCompleted(c => (c < 100 ? c + 1 : 100));
        }, 500); // 0.5s per item
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col items-center gap-4 text-white">
            <div className="text-xl font-mono">
                {completed}/100 items
            </div>
            <EstimatedTime
                startTime={startTime}
                totalItems={100}
                completedItems={completed}
            />
        </div>
    );
};

export const Static: Story = {
    args: {
        startTime: new Date(Date.now() - 10000), // Started 10s ago
        totalItems: 100,
        completedItems: 10, // 10 items in 10s = 1s/item. Remaining 90 = 90s.
    },
};

export const LiveSimulation: Story = {
    render: () => <ProgressSimulation />,
};
