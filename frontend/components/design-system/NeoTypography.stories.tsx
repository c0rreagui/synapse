import type { Meta, StoryObj } from '@storybook/react';
import { NeoTypography } from './NeoTypography';

const meta: Meta<typeof NeoTypography> = {
    title: 'Design System/Atoms/NeoTypography',
    component: NeoTypography,
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: { type: 'select' },
            options: ['h1', 'h2', 'h3', 'body', 'caption'],
        },
        glow: {
            control: { type: 'select' },
            options: ['none', 'primary', 'secondary'],
        },
        gradient: {
            control: 'boolean'
        }
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' }
    },
};

export default meta;
type Story = StoryObj<typeof NeoTypography>;

export const Heading1: Story = {
    args: {
        variant: 'h1',
        children: 'Protocol Initiated',
    },
};

export const WithGradient: Story = {
    args: {
        variant: 'h1',
        gradient: true,
        children: 'NEO-GLASS UI',
    },
};

export const WithGlow: Story = {
    args: {
        variant: 'h2',
        glow: 'primary',
        children: 'System Online',
    },
};

export const BodyText: Story = {
    args: {
        variant: 'body',
        children: 'The neural interface connects the user directly to the core processing unit, bypassing traditional input latency.',
        className: "max-w-md text-center"
    },
};
