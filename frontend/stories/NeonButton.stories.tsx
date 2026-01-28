import type { Meta, StoryObj } from '@storybook/nextjs';
import { NeonButton } from '../app/components/NeonButton';


const meta: Meta<typeof NeonButton> = {
    title: 'App/Atoms/NeonButton',
    component: NeonButton,
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: 'select',
            options: ['primary', 'ghost', 'danger'],
        },
        disabled: { control: 'boolean' },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof NeonButton>;

export const Primary: Story = {
    args: {
        variant: 'primary',
        children: 'Launch Protocol',
    },
};

export const Ghost: Story = {
    args: {
        variant: 'ghost',
        children: 'Cancel Operation',
    },
};

export const Danger: Story = {
    args: {
        variant: 'danger',
        children: 'Delete System 32',
    },
};

export const Loading: Story = {
    args: {
        variant: 'primary',
        children: 'Processing...',
        disabled: true,
    },
};
