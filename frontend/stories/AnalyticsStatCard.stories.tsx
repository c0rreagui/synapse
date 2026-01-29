import type { Meta, StoryObj } from '@storybook/react';
import { StatCard } from '../app/components/analytics/StatCard';
import { Users, DollarSign, Activity, TrendingUp } from 'lucide-react';

const meta: Meta<typeof StatCard> = {
    title: 'App/Analytics/StatCard (Simple)',
    component: StatCard,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    argTypes: {
        color: {
            control: 'select',
            options: ['purple', 'green', 'pink', 'blue'],
        },
        trend: {
            control: 'select',
            options: ['up', 'down', 'neutral'],
        },
    },
};

export default meta;
type Story = StoryObj<typeof StatCard>;

export const Purple: Story = {
    args: {
        label: 'Total Users',
        value: '12,345',
        subValue: 'Active in last 30 days',
        trend: 'up',
        trendValue: '12%',
        icon: <Users className="w-5 h-5" />,
        color: 'purple',
    },
};

export const Green: Story = {
    args: {
        label: 'Revenue',
        value: '$45,200',
        subValue: 'Gross income',
        trend: 'up',
        trendValue: '8.5%',
        icon: <DollarSign className="w-5 h-5" />,
        color: 'green',
    },
};

export const Pink: Story = {
    args: {
        label: 'Bounce Rate',
        value: '42.3%',
        subValue: 'Average per session',
        trend: 'down',
        trendValue: '2.1%',
        icon: <Activity className="w-5 h-5" />,
        color: 'pink',
    },
};

export const Blue: Story = {
    args: {
        label: 'Growth',
        value: '+145',
        subValue: 'New subscribers',
        trend: 'neutral',
        trendValue: '0%',
        icon: <TrendingUp className="w-5 h-5" />,
        color: 'blue',
    },
};
