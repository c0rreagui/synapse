import type { Meta, StoryObj } from '@storybook/nextjs';
import Skeleton, { CardSkeleton, ListItemSkeleton } from '../app/components/Skeleton';

const meta: Meta<typeof Skeleton> = {
    title: 'App/Atoms/Skeleton',
    component: Skeleton,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Skeleton>;

export const Default: Story = {
    args: {
        width: 200,
        height: 20,
        borderRadius: 4,
    },
};

export const Circle: Story = {
    args: {
        width: 50,
        height: 50,
        borderRadius: 25,
    },
};

export const CardPreset: Story = {
    render: () => <CardSkeleton />,
};

export const ListPreset: Story = {
    render: () => (
        <div className="space-y-2">
            <ListItemSkeleton />
            <ListItemSkeleton />
            <ListItemSkeleton />
        </div>
    ),
};
