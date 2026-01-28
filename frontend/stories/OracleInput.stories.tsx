import type { Meta, StoryObj } from '@storybook/nextjs';
import { OracleInput } from '../app/components/oracle/OracleInput';

const meta: Meta<typeof OracleInput> = {
    title: 'App/Features/Oracle/OracleInput',
    component: OracleInput,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-full max-w-4xl mx-auto py-20">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof OracleInput>;

export const Default: Story = {
    args: {
        isLoading: false,
        onAnalyze: (username) => alert(`Analyzing ${username}...`),
    },
};

export const Loading: Story = {
    args: {
        isLoading: true,
        onAnalyze: () => { },
    },
};
