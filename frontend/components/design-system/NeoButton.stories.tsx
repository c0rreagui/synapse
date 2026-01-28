import type { Meta, StoryObj } from '@storybook/react';
import { NeoButton } from './NeoButton';
import { User, Sparkles, Trash2 } from 'lucide-react';

const meta: Meta<typeof NeoButton> = {
    title: 'Design System/Atoms/NeoButton',
    component: NeoButton,
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: { type: 'select' },
            options: ['primary', 'secondary', 'ghost', 'danger'],
        },
        size: {
            control: { type: 'select' },
            options: ['sm', 'md', 'lg', 'icon'],
        },
        glow: {
            control: 'boolean',
        },
    },
    parameters: {
        layout: 'centered',
        backgrounds: {
            default: 'dark',
        }
    },
};

export default meta;
type Story = StoryObj<typeof NeoButton>;

export const Primary: Story = {
    args: {
        variant: 'primary',
        children: 'Launch Protocol',
    },
};

export const Secondary: Story = {
    args: {
        variant: 'secondary',
        children: 'System Check',
    },
};

export const Ghost: Story = {
    args: {
        variant: 'ghost',
        children: 'Dismiss',
    },
};

export const Danger: Story = {
    args: {
        variant: 'danger',
        children: (
            <span className="flex items-center gap-2">
                <Trash2 size={16} />
                Terminate Process
            </span>
        ),
    },
};

export const Loading: Story = {
    args: {
        variant: 'primary',
        isLoading: true,
        children: 'Processing...',
    },
};

export const WithIcon: Story = {
    args: {
        variant: 'primary',
        children: (
            <>
                <Sparkles className="mr-2 h-4 w-4" />
                AI Generate
            </>
        ),
    },
};

export const IconOnly: Story = {
    args: {
        variant: 'secondary',
        size: 'icon',
        children: <User className="h-5 w-5" />,
    },
};
