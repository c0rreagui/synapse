import type { Meta, StoryObj } from '@storybook/nextjs';
import { InsightCard } from '../app/components/oracle/InsightCard';
import { LightBulbIcon, ChartBarIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof InsightCard> = {
    title: 'App/Features/Oracle/InsightCard',
    component: InsightCard,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof InsightCard>;

export const Default: Story = {
    args: {
        title: 'Key Takeaways',
        items: [
            'Retention drops significantly after 0:15s.',
            'Users love the new dark mode aesthetic.',
            'Mobile traffic increased by 20% this week.'
        ],
        icon: <LightBulbIcon className="w-6 h-6" />,
    },
};

export const PerformanceMetrics: Story = {
    args: {
        title: 'Performance Goals',
        items: [
            'CPU usage stabilized below 40%.',
            'Queue processing speed up 2x.',
            'Memory leaks patched in worker node.'
        ],
        icon: <ChartBarIcon className="w-6 h-6" />,
    },
};
