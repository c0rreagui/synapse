import type { Meta, StoryObj } from '@storybook/nextjs';
import FadeIn from '../app/components/FadeIn';

const meta: Meta<typeof FadeIn> = {
    title: 'App/Utilities/FadeIn',
    component: FadeIn,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof FadeIn>;

export const Default: Story = {
    args: {
        children: <div className="p-4 bg-synapse-purple text-white rounded-lg">I fade in nicely!</div>,
        delay: 0,
        duration: 800,
        direction: 'up',
    },
};

export const Delayed: Story = {
    args: {
        children: <div className="p-4 bg-synapse-cyan text-white rounded-lg">I wait 1s before showing up</div>,
        delay: 1000,
        duration: 500,
        direction: 'down',
    },
};

export const SlideRight: Story = {
    args: {
        children: <div className="p-4 bg-orange-500 text-white rounded-lg">I slide from the left</div>,
        direction: 'right',
        distance: 50,
    },
};
