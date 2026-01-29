import type { Meta, StoryObj } from '@storybook/react';
import AmbientBackground from '../app/components/AmbientBackground';

const meta = {
    title: 'Atoms/Visuals/AmbientBackground',
    component: AmbientBackground,
    parameters: {
        layout: 'fullscreen',
    },
    tags: ['autodocs'],
    decorators: [
        (Story) => (
            <div className="relative h-[400px] w-full bg-[#050505] overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center z-10">
                    <h1 className="text-white text-2xl font-bold opacity-80 mix-blend-overlay">Background Content</h1>
                </div>
                <Story />
            </div>
        ),
    ],
} satisfies Meta<typeof AmbientBackground>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithDarkerContext: Story = {
    decorators: [
        (Story) => (
            <div className="relative h-[400px] w-full bg-black overflow-hidden">
                <Story />
            </div>
        ),
    ],
};
