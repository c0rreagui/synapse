import type { Meta, StoryObj } from '@storybook/nextjs';
import Parallax from '../app/components/Parallax';

const meta: Meta<typeof Parallax> = {
    title: 'App/Utilities/Parallax',
    component: Parallax,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen', // Fullscreen to allow scrolling
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div style={{ height: '200vh', padding: '50px' }}>
                <p className="text-gray-500 mb-10">Scroll down to see the effect...</p>
                <Story />
                <p className="text-gray-500 mt-[1000px]">Keep scrolling...</p>
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof Parallax>;

export const Default: Story = {
    args: {
        speed: 0.5,
        children: (
            <div className="w-48 h-48 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-xl shadow-2xl flex items-center justify-center text-white font-bold text-xl">
                I Move Slow
            </div>
        ),
    },
};

export const FastReverse: Story = {
    args: {
        speed: 1.2,
        direction: 'down',
        children: (
            <div className="w-48 h-48 bg-gradient-to-br from-pink-500 to-rose-500 rounded-full shadow-2xl flex items-center justify-center text-white font-bold text-xl ml-64">
                I Move Fast
            </div>
        ),
    },
};
