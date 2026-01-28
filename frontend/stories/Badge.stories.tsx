import type { Meta, StoryObj } from '@storybook/nextjs';
import Badge from '../app/components/Badge';

const meta: Meta<typeof Badge> = {
    title: 'App/Atoms/Badge',
    component: Badge,
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: 'select',
            options: ['success', 'error', 'warning', 'info', 'neutral'],
        },
        size: {
            control: 'select',
            options: ['sm', 'md'],
        },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Success: Story = {
    args: {
        children: 'Completed',
        variant: 'success',
        dot: true,
    },
};

export const Error: Story = {
    args: {
        children: 'Failed',
        variant: 'error',
        dot: true,
    },
};

export const Warning: Story = {
    args: {
        children: 'Pending',
        variant: 'warning',
        dot: true,
    },
};

export const Info: Story = {
    args: {
        children: 'Processing',
        variant: 'info',
        dot: false,
    },
};

export const Neutral: Story = {
    args: {
        children: 'Draft',
        variant: 'neutral',
        size: 'sm',
    },
};
