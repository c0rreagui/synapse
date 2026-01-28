import type { Meta, StoryObj } from '@storybook/nextjs';
import { StitchCard } from '../app/components/StitchCard';

const meta: Meta<typeof StitchCard> = {
    title: 'App/Molecules/StitchCard',
    component: StitchCard,
    tags: ['autodocs'],
    argTypes: {
        hoverEffect: { control: 'boolean' },
        noPadding: { control: 'boolean' },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div style={{ width: '400px' }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof StitchCard>;

export const Default: Story = {
    args: {
        children: (
            <div>
                <h3 className="text-white font-bold text-lg mb-2">System Status</h3>
                <p className="text-gray-400 text-sm">All systems operational. Network latency optimized for deep space communication.</p>
            </div>
        ),
    },
};

export const NoHoverEffect: Story = {
    args: {
        hoverEffect: false,
        children: (
            <div>
                <h3 className="text-white font-bold text-lg mb-2">Static Panel</h3>
                <p className="text-gray-400 text-sm">This card does not react to hover events. Useful for static information display.</p>
            </div>
        ),
    },
};

export const NoPadding: Story = {
    args: {
        noPadding: true,
        children: (
            <div className="flex flex-col">
                <div className="bg-white/5 p-4 border-b border-white/5">
                    <h3 className="text-white font-bold">Header Section</h3>
                </div>
                <div className="p-4">
                    <p className="text-gray-400 text-sm">Content with custom internal padding structure.</p>
                </div>
            </div>
        ),
    },
};
