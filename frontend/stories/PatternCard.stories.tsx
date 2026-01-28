import type { Meta, StoryObj } from '@storybook/nextjs';
import { PatternCard } from '../app/components/oracle/PatternCard';

const meta: Meta<typeof PatternCard> = {
    title: 'App/Features/Oracle/PatternCard',
    component: PatternCard,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[400px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof PatternCard>;

export const ViralHook: Story = {
    args: {
        type: 'VIRAL_HOOK',
        title: 'Unexpected Transition',
        description: 'Videos starting with a sudden visual change in the first 3 seconds are showing 40% higher retention.',
        confidence: 92,
        impact: 'HIGH',
    },
};

export const TimingPattern: Story = {
    args: {
        type: 'TIMING',
        title: 'Golden Hour Posting',
        description: 'Posts published between 18:00 and 20:00 EST are getting 2x more initial traction.',
        confidence: 78,
        impact: 'MEDIUM',
    },
};

export const Anomaly: Story = {
    args: {
        type: 'ANOMALY',
        title: 'Drop in Engagement',
        description: 'Sudden decrease in comments on tutorial videos despite high view counts.',
        confidence: 85,
        impact: 'LOW',
    },
};
