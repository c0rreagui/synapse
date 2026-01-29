import type { Meta, StoryObj } from '@storybook/react';
import ScrollProgress from '../app/components/ScrollProgress';

const meta: Meta<typeof ScrollProgress> = {
    title: 'App/Molecules/ScrollProgress',
    component: ScrollProgress,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    argTypes: {
        position: { control: 'radio', options: ['top', 'bottom'] },
        color: { control: 'color' },
        height: { control: { type: 'range', min: 1, max: 10 } },
    }
};

export default meta;
type Story = StoryObj<typeof ScrollProgress>;

export const Default: Story = {
    render: (args) => (
        <div className="min-h-screen">
            <ScrollProgress {...args} />

            <div className="max-w-2xl mx-auto py-20 px-8 space-y-8">
                <h1 className="text-4xl font-bold text-white mb-8">Scroll Down</h1>

                {Array.from({ length: 20 }).map((_, i) => (
                    <div key={i} className="p-6 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm">
                        <h3 className="text-xl font-semibold text-white mb-2">Section {i + 1}</h3>
                        <p className="text-white/60">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
                        </p>
                    </div>
                ))}
            </div>
        </div>
    ),
    args: {
        color: '#06b6d4', // Cyan
        height: 3,
        position: 'top'
    }
};
