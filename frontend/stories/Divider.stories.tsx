import type { Meta, StoryObj } from '@storybook/nextjs';
import Divider from '../app/components/Divider';

const meta: Meta<typeof Divider> = {
    title: 'App/Atoms/Divider',
    component: Divider,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-full h-32 flex flex-col justify-center text-white">
                <p>Content Above</p>
                <Story />
                <p>Content Below</p>
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof Divider>;

export const Horizontal: Story = {
    args: {
        orientation: 'horizontal',
        spacing: 'md',
    },
};

export const WithLabel: Story = {
    args: {
        orientation: 'horizontal',
        spacing: 'md',
        label: 'Section Title',
    },
};

export const Vertical: Story = {
    decorators: [
        (Story) => (
            <div className="flex h-10 items-center text-white">
                <span>Left</span>
                <Story />
                <span>Right</span>
            </div>
        ),
    ],
    args: {
        orientation: 'vertical',
        spacing: 'md',
    },
};
