import type { Meta, StoryObj } from '@storybook/nextjs';
import ProgressBar from '../app/components/ProgressBar';

const meta: Meta<typeof ProgressBar> = {
    title: 'App/Atoms/ProgressBar',
    component: ProgressBar,
    tags: ['autodocs'],
    argTypes: {
        progress: { control: { type: 'range', min: 0, max: 100 } },
        color: { control: 'color' },
        height: { control: 'number' },
    },
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[300px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof ProgressBar>;

export const Default: Story = {
    args: {
        progress: 45,
    },
};

export const High: Story = {
    args: {
        progress: 88,
        color: '#f85149',
    },
};

export const Slim: Story = {
    args: {
        progress: 60,
        height: 4,
        showPercent: false,
        color: '#a371f7',
    },
};
