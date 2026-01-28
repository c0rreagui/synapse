import type { Meta, StoryObj } from '@storybook/nextjs';
import AnimatedCounter from '../app/components/AnimatedCounter';

const meta: Meta<typeof AnimatedCounter> = {
    title: 'App/Atoms/AnimatedCounter',
    component: AnimatedCounter,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof AnimatedCounter>;

export const Default: Story = {
    args: {
        value: 1000,
        duration: 2000,
    },
};

export const Currency: Story = {
    args: {
        prefix: '$',
        value: 5432,
        duration: 1500,
        style: { fontSize: '24px', fontWeight: 'bold', color: '#4ade80' },
    },
};

export const WithDecimals: Story = {
    args: {
        value: 98.6,
        decimals: 1,
        suffix: '%',
        style: { fontSize: '32px', color: '#60a5fa' },
    },
};
