import type { Meta, StoryObj } from '@storybook/nextjs';
import { PerformanceChart } from '../app/components/analytics/PerformanceChart';

const meta: Meta<typeof PerformanceChart> = {
    title: 'App/Features/Analytics/PerformanceChart',
    component: PerformanceChart,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[800px] bg-black/40 p-4 rounded-xl border border-white/10">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof PerformanceChart>;

const generateData = (days: number) => Array.from({ length: days }, (_, i) => ({
    date: `Mar ${i + 1}`,
    views: Math.floor(Math.random() * 10000) + 5000 + Math.sin(i) * 2000,
}));

export const Default: Story = {
    args: {
        data: generateData(14),
    },
};

export const HighTraffic: Story = {
    args: {
        data: generateData(30).map(d => ({ ...d, views: d.views * 5 })),
    },
};

export const Empty: Story = {
    args: {
        data: [],
    },
};
