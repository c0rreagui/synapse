import type { Meta, StoryObj } from '@storybook/nextjs';
import RippleButton from '../app/components/RippleButton';
import { HomeIcon, CogIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof RippleButton> = {
    title: 'App/Atoms/RippleButton',
    component: RippleButton,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    argTypes: {
        onClick: { action: 'clicked' },
    },
};

export default meta;
type Story = StoryObj<typeof RippleButton>;

export const Primary: Story = {
    args: {
        children: 'Click Me',
        variant: 'primary',
    },
};

export const Secondary: Story = {
    args: {
        children: 'Secondary Action',
        variant: 'secondary',
    },
};

export const Danger: Story = {
    args: {
        children: 'Delete Item',
        variant: 'danger',
    },
};

export const Ghost: Story = {
    args: {
        children: 'Cancel',
        variant: 'ghost',
    },
};

export const WithIcon: Story = {
    args: {
        children: 'Dashboard',
        icon: <HomeIcon style={{ width: 16, height: 16 }} />,
        variant: 'primary',
    },
};

export const Loading: Story = {
    args: {
        children: 'Saving...',
        loading: true,
    },
};

export const FullWidth: Story = {
    decorators: [(Story) => <div className="w-64"><Story /></div>],
    args: {
        children: 'Full Width Button',
        fullWidth: true,
    },
};
