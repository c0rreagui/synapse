import type { Meta, StoryObj } from '@storybook/nextjs';
import PasswordStrength from '../app/components/PasswordStrength';
import FormInput from '../app/components/FormInput';
import { useState } from 'react';

const meta: Meta<typeof PasswordStrength> = {
    title: 'App/Utilities/PasswordStrength',
    component: PasswordStrength,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof PasswordStrength>;

export const Interactive = {
    render: () => {
        const [password, setPassword] = useState('');
        return (
            <div className="w-80 p-4 bg-slate-900 rounded-lg">
                <FormInput
                    label="New Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Type to test strength..."
                />
                <PasswordStrength password={password} />
            </div>
        );
    }
};

export const Weak: Story = {
    args: { password: '123' },
    decorators: [(Story) => <div className="w-64"><Story /></div>]
};

export const Medium: Story = {
    args: { password: 'password123' },
    decorators: [(Story) => <div className="w-64"><Story /></div>]
};

export const Strong: Story = {
    args: { password: 'Correct-Horse-Battery-Staple-99!' },
    decorators: [(Story) => <div className="w-64"><Story /></div>]
};
