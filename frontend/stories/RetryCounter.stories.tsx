import type { Meta, StoryObj } from '@storybook/react';
import RetryCounter from '../app/components/RetryCounter';
import { useState } from 'react';

const meta: Meta<typeof RetryCounter> = {
    title: 'App/Molecules/RetryCounter',
    component: RetryCounter,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    argTypes: {
        children: { control: 'text' },
        maxRetries: { control: { type: 'number', min: 1, max: 10 } },
    }
};

export default meta;
type Story = StoryObj<typeof RetryCounter>;

// Mock component to simulate retry success/failure
const RetrySimulation = ({ failCount = 2, ...props }: { failCount?: number } & React.ComponentProps<typeof RetryCounter>) => {
    let attempts = 0;

    // We need to pass a promise returning function
    const simulateRequest = async () => {
        attempts++;
        await new Promise(resolve => setTimeout(resolve, 1000));

        console.log(`Attempt ${attempts}, need > ${failCount} to succeed`);
        return attempts > failCount;
    };

    return (
        <RetryCounter {...props} onRetry={simulateRequest}>
            <div className="text-white/80">
                <p className="font-medium text-red-400">Connection Failed</p>
                <p className="text-sm">Server responded with 503 Service Unavailable</p>
            </div>
        </RetryCounter>
    );
};

export const Default: Story = {
    render: (args) => <RetrySimulation {...args} />,
    args: {
        maxRetries: 3,
        failCount: 1, // Succeeds on 2nd try
    }
};

export const MaxRetriesReached: Story = {
    render: (args) => <RetrySimulation {...args} />,
    args: {
        maxRetries: 3,
        failCount: 4, // Always fails until max retries
    }
};

export const CustomMessage: Story = {
    render: (args) => (
        <RetryCounter {...args} onRetry={async () => false}>
            <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-white">Live Feed Disconnected</span>
            </div>
        </RetryCounter>
    ),
    args: {
        maxRetries: 5
    }
};
