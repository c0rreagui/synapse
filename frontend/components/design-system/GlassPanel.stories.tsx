import type { Meta, StoryObj } from '@storybook/react';
import { GlassPanel } from './GlassPanel';

const meta: Meta<typeof GlassPanel> = {
    title: 'Design System/Atoms/GlassPanel',
    component: GlassPanel,
    tags: ['autodocs'],
    argTypes: {
        intensity: {
            control: { type: 'select' },
            options: ['low', 'medium', 'high'],
        },
        border: {
            control: 'boolean'
        }
    },
    parameters: {
        layout: 'padded',
        backgrounds: {
            default: 'dark', // Crucial to see opacity
        }
    },
};

export default meta;
type Story = StoryObj<typeof GlassPanel>;

export const Default: Story = {
    args: {
        children: (
            <div className="p-8 text-neo-primary">
                <h3 className="text-xl font-bold mb-2">Neo-Glass Container</h3>
                <p className="text-gray-400">This panel uses the standard "Medium" intensity with a backdrop blur.</p>
            </div>
        ),
        className: "max-w-md"
    },
};

export const HighIntensity: Story = {
    args: {
        intensity: 'high',
        children: (
            <div className="p-8">
                <h3 className="text-xl font-bold mb-2 text-white">High Privacy</h3>
                <p className="text-gray-400">Less transparency, higher blur for overlay content.</p>
            </div>
        ),
        className: "max-w-md"
    },
};

export const NoBorder: Story = {
    args: {
        border: false,
        intensity: 'low',
        children: (
            <div className="p-8">
                <h3 className="text-xl font-bold mb-2 text-neo-secondary">Ghost Panel</h3>
                <p className="text-gray-400">Used for subtle grouping without hard edges.</p>
            </div>
        ),
        className: "max-w-md"
    },
};
