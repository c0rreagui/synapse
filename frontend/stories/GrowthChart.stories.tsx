import type { Meta, StoryObj } from '@storybook/nextjs';
import GrowthChart from '../app/components/analytics/GrowthChart';

const meta: Meta<typeof GrowthChart> = {
    title: 'App/Features/Analytics/GrowthChart',
    component: GrowthChart,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[800px] h-[400px] bg-black/40 p-4 rounded-xl border border-white/10">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof GrowthChart>;

const generateData = (days: number) => Array.from({ length: days }, (_, i) => ({
    date: `2024-03-${String(i + 1).padStart(2, '0')}`,
    views: Math.floor(Math.random() * 5000) + 1000 + (i * 100),
    likes: Math.floor(Math.random() * 1000) + 100 + (i * 20),
}));

export const MonthlyGrowth: Story = {
    args: {
        data: generateData(30),
    },
};

export const QuarterlyGrowth: Story = {
    args: {
        data: generateData(90),
    },
};

export const NoData: Story = {
    args: {
        data: [],
    },
};
