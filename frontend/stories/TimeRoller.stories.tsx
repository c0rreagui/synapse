import type { Meta, StoryObj } from '@storybook/nextjs';
import TimeRoller from '../app/components/TimeRoller';
import { useState } from 'react';

const meta: Meta<typeof TimeRoller> = {
    title: 'App/Utilities/TimeRoller',
    component: TimeRoller,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof TimeRoller>;

export const Interactive = {
    render: () => {
        const [time, setTime] = useState('');
        const [isScheduled, setIsScheduled] = useState(false);

        return (
            <div className="flex flex-col items-center gap-6 p-6 bg-slate-900 rounded-xl border border-white/5">
                <div className="text-center">
                    <h3 className="text-white font-bold mb-1">Schedule Post</h3>
                    <p className="text-xs text-slate-400">
                        {isScheduled ? `Scheduled for: ${time}` : 'Posting immediately'}
                    </p>
                </div>

                <TimeRoller
                    onChange={(t, scheduled) => {
                        setTime(t);
                        setIsScheduled(scheduled);
                    }}
                />
            </div>
        );
    }
};
