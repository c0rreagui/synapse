import type { Meta, StoryObj } from '@storybook/nextjs';
import { MetricComparisonChart } from '../app/components/oracle/MetricComparisonChart';

const meta: Meta<typeof MetricComparisonChart> = {
    title: 'App/Features/Oracle/MetricComparisonChart',
    component: MetricComparisonChart,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[600px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;

export const Default = {
    args: {
        data: [
            { period: '7d', current: 15400, previous: 12000 },
            { period: '30d', current: 85000, previous: 92000 },
            { period: '90d', current: 240000, previous: 180000 },
        ],
    },
};

export const Improving = {
    args: {
        data: [
            { period: '7d', current: 20000, previous: 10000 },
            { period: '30d', current: 90000, previous: 60000 },
            { period: '90d', current: 300000, previous: 200000 },
        ],
    },
};

