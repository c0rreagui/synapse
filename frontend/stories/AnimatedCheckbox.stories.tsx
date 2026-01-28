import type { Meta, StoryObj } from '@storybook/nextjs';
import AnimatedCheckbox from '../app/components/AnimatedCheckbox';
import { useState } from 'react';

const meta: Meta<typeof AnimatedCheckbox> = {
    title: 'App/Atoms/AnimatedCheckbox',
    component: AnimatedCheckbox,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof AnimatedCheckbox>;

export const Interactive = {
    render: () => {
        const [checked, setChecked] = useState(false);
        return (
            <AnimatedCheckbox
                checked={checked}
                onChange={setChecked}
                label="Enable Awesome Mode"
            />
        );
    }
};

export const Checked: Story = {
    args: {
        checked: true,
        label: 'Task Completed',
        onChange: () => { },
    },
};

export const Disabled: Story = {
    args: {
        checked: false,
        label: 'Locked Option',
        disabled: true,
        onChange: () => { },
    },
};
