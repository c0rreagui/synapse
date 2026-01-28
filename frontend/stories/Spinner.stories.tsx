import type { Meta, StoryObj } from '@storybook/nextjs';
import Spinner from '../app/components/Spinner';

const meta: Meta<typeof Spinner> = {
    title: 'App/Atoms/Spinner',
    component: Spinner,
    tags: ['autodocs'],
    argTypes: {
        size: {
            control: 'select',
            options: ['sm', 'md', 'lg'],
        },
        color: { control: 'color' },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Spinner>;

export const Default: Story = {
    args: {
        size: 'md',
    },
};

export const Small: Story = {
    args: {
        size: 'sm',
    },
};

export const Large: Story = {
    args: {
        size: 'lg',
        color: '#f85149',
    },
};
