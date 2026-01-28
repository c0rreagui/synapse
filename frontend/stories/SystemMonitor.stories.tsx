import type { Meta, StoryObj } from '@storybook/nextjs';
import SystemMonitor from '../app/components/SystemMonitor';

const meta: Meta<typeof SystemMonitor> = {
    title: 'App/Molecules/SystemMonitor',
    component: SystemMonitor,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[300px] p-4 bg-black/50 border border-white/10 rounded-xl">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof SystemMonitor>;

export const Healthy: Story = {
    args: {
        system: {
            cpu_percent: 12.5,
            ram_percent: 34.2,
            disk_usage: 45.0,
        },
    },
};

export const HighLoad: Story = {
    args: {
        system: {
            cpu_percent: 85.0,
            ram_percent: 78.5,
            disk_usage: 60.0,
        },
    },
};

export const Critical: Story = {
    args: {
        system: {
            cpu_percent: 98.2,
            ram_percent: 95.1,
            disk_usage: 92.0,
        },
    },
};

export const Idle: Story = {
    args: {
        system: {
            cpu_percent: 1.2,
            ram_percent: 15.0,
            disk_usage: 45.0,
        },
    },
};
