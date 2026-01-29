import type { Meta, StoryObj } from '@storybook/nextjs';
import StatCard from '../app/components/StatCard';
import { ArrowTrendingUpIcon, UserGroupIcon, CurrencyDollarIcon, EyeIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof StatCard> = {
    title: 'App/Molecules/StatCard (Aurora)',
    component: StatCard,
    tags: ['autodocs'],
    argTypes: {
        color: {
            control: 'select',
            options: ['magenta', 'violet', 'teal', 'mint'],
        },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[300px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof StatCard>;

export const Violet: Story = {
    args: {
        label: 'Total Views',
        value: '2.4M',
        trend: '+12.5%',
        icon: EyeIcon,
        color: 'violet',
    },
};

export const Magenta: Story = {
    args: {
        label: 'Engagement',
        value: '85.2%',
        trend: '+4.3%',
        icon: UserGroupIcon,
        color: 'magenta',
    },
};

export const Teal: Story = {
    args: {
        label: 'Revenue',
        value: '$12,450',
        trend: '+8.1%',
        icon: CurrencyDollarIcon,
        color: 'teal',
    },
};

export const Mint: Story = {
    args: {
        label: 'Growth Score',
        value: '98/100',
        trend: '+2pts',
        icon: ArrowTrendingUpIcon,
        color: 'mint',
    },
};
