import type { Meta, StoryObj } from '@storybook/nextjs';
import { EngagementHeatmap } from '../app/components/oracle/EngagementHeatmap';

const meta: Meta<typeof EngagementHeatmap> = {
    title: 'App/Features/Oracle/EngagementHeatmap',
    component: EngagementHeatmap,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[600px] bg-black/50 p-4 rounded-xl">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof EngagementHeatmap>;

const generateData = (base: number) => Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    intensity: Math.max(10, Math.min(100, base + Math.sin(i / 3) * 40 + (Math.random() * 20 - 10)))
}));

export const Default: Story = {
    args: {
        data: generateData(50),
    },
};

export const HighEngagement: Story = {
    args: {
        data: generateData(80),
    },
};

export const LowEngagement: Story = {
    args: {
        data: generateData(20),
    },
};
