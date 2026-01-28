import type { Meta, StoryObj } from '@storybook/react';
import { StitchCard } from './StitchCard';
import { NeoTypography } from './NeoTypography';
import { NeoButton } from './NeoButton';

const meta: Meta<typeof StitchCard> = {
    title: 'Design System/Molecules/StitchCard',
    component: StitchCard,
    tags: ['autodocs'],
    argTypes: {
        hoverEffect: { control: 'boolean' },
        noPadding: { control: 'boolean' }
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' }
    },
};

export default meta;
type Story = StoryObj<typeof StitchCard>;

export const Default: Story = {
    args: {
        children: (
            <div className="flex flex-col gap-4">
                <NeoTypography variant="h3" glow="primary">Holographic Module</NeoTypography>
                <NeoTypography variant="body">
                    This card implements the high-fidelity "Stitch" visual language:
                    holographic grid background, scanline overlays, and ambient light bloom.
                </NeoTypography>
                <NeoButton variant="secondary" size="sm" className="w-full mt-2">Interact</NeoButton>
            </div>
        ),
        className: "w-[400px]"
    },
};

export const NoPadding: Story = {
    args: {
        noPadding: true,
        children: (
            <div>
                <div className="h-32 bg-neo-primary/20 flex items-center justify-center border-b border-white/5">
                    <span className="text-neo-primary font-mono text-xs">COVER_IMAGE_PLACEHOLDER</span>
                </div>
                <div className="p-6">
                    <NeoTypography variant="h3">Compact View</NeoTypography>
                    <NeoTypography variant="caption" className="mt-2">System Status: Optimal</NeoTypography>
                </div>
            </div>
        ),
        className: "w-[300px]"
    },
};
