import type { Meta, StoryObj } from '@storybook/nextjs';
import ScrollProgress from '../app/components/ScrollProgress';

const meta: Meta<typeof ScrollProgress> = {
    title: 'App/Utilities/ScrollProgress',
    component: ScrollProgress,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="h-[300vh] w-full bg-gray-900 text-white p-8">
                <Story />
                <h1 className="text-4xl mb-8">Long Content Page</h1>
                <p className="text-lg opacity-50">Scroll down to see the progress bar at the top moving.</p>
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof ScrollProgress>;

export const Cyan: Story = {
    args: {
        color: '#00f3ff',
        height: 4,
        position: 'top',
    },
};

export const PurpleBottom: Story = {
    args: {
        color: '#8b5cf6',
        height: 6,
        position: 'bottom',
    },
};
