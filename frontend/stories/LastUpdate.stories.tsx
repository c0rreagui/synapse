import type { Meta, StoryObj } from '@storybook/nextjs';
import LastUpdate from '../app/components/LastUpdate';

const meta: Meta<typeof LastUpdate> = {
    title: 'App/Molecules/LastUpdate',
    component: LastUpdate,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof LastUpdate>;

const now = new Date();
const fiveMinAgo = new Date(now.getTime() - 5 * 60 * 1000);
const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);

export const JustNow: Story = {
    args: {
        timestamp: now,
    },
};

export const FiveMinutesAgo: Story = {
    args: {
        timestamp: fiveMinAgo,
    },
};

export const TwoHoursAgo: Story = {
    args: {
        timestamp: twoHoursAgo,
    },
};

export const CustomPrefix: Story = {
    args: {
        timestamp: now,
        prefix: 'Last synced:',
        showIcon: false,
    },
};
