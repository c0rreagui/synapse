import type { Meta, StoryObj } from '@storybook/nextjs';
import GlassCard from '../app/components/GlassCard';
import { NeoButton } from '../components/design-system/NeoButton';

const meta: Meta<typeof GlassCard> = {
    title: 'App/Molecules/GlassCard',
    component: GlassCard,
    tags: ['autodocs'],
    argTypes: {
        glow: {
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
            <div className="w-[400px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof GlassCard>;

export const Default: Story = {
    args: {
        title: 'Project Alpha',
        subtitle: 'Core Systems',
        children: (
            <div className="space-y-4 text-gray-400 text-sm">
                <p>This is a standard glass card used for grouping content.</p>
                <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full w-2/3 bg-white/20"></div>
                </div>
            </div>
        ),
    },
};

export const WithAction: Story = {
    args: {
        title: 'Deployment Ready',
        subtitle: 'Production Environment',
        glow: 'teal',
        action: <NeoButton size="sm" variant="secondary">Deploy</NeoButton>,
        children: (
            <p className="text-gray-400 text-sm">
                Build #420 is ready for deployment. All systems checks passed.
            </p>
        ),
    },
};

export const MagentaGlow: Story = {
    args: {
        title: 'Critical Alert',
        glow: 'magenta',
        children: (
            <p className="text-gray-400 text-sm">
                System resources are running low. Please investgiate immediately.
            </p>
        ),
    },
};

export const MintGlow: Story = {
    args: {
        title: 'Optimization Complete',
        glow: 'mint',
        children: (
            <p className="text-gray-400 text-sm">
                Performance boosted by 20% after latest patch.
            </p>
        ),
    },
};
