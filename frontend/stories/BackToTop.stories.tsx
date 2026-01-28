import type { Meta, StoryObj } from '@storybook/nextjs';
import BackToTop from '../app/components/BackToTop';

const meta: Meta<typeof BackToTop> = {
    title: 'App/Utilities/BackToTop',
    component: BackToTop,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen', // Needed to scroll
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="h-[200vh] w-full p-4 text-white">
                <h1 className="text-2xl mb-4">Scroll Down to see the button</h1>
                <p className="mb-[100vh]">Keep scrolling...</p>
                <p>You can see me now!</p>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof BackToTop>;

export const Default: Story = {
    args: {
        threshold: 100,
        smooth: true,
    },
};
