import type { Meta, StoryObj } from '@storybook/nextjs';
import Toggle from '../app/components/Toggle';
import { useState } from 'react';

const meta: Meta<typeof Toggle> = {
    title: 'App/Atoms/Toggle',
    component: Toggle,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Toggle>;

export const Default: Story = {
    args: {
        checked: false,
        label: 'Enable Feature',
        id: 'toggle-1',
    },
    render: (args) => {
        const [checked, setChecked] = useState(args.checked);
        return <Toggle {...args} checked={checked} onChange={setChecked} />;
    },
};

export const Checked: Story = {
    args: {
        checked: true,
        label: 'Active Feature',
        id: 'toggle-2',
    },
    render: (args) => {
        const [checked, setChecked] = useState(args.checked);
        return <Toggle {...args} checked={checked} onChange={setChecked} />;
    },
};

export const Disabled: Story = {
    args: {
        checked: false,
        disabled: true,
        label: 'Disabled Feature',
        id: 'toggle-3',
    },
};
