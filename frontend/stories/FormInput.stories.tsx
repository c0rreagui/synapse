import type { Meta, StoryObj } from '@storybook/nextjs';
import FormInput from '../app/components/FormInput';

const meta: Meta<typeof FormInput> = {
    title: 'App/Atoms/FormInput',
    component: FormInput,
    tags: ['autodocs'],
    argTypes: {
        type: {
            control: 'select',
            options: ['text', 'password', 'email', 'number'],
        },
        disabled: { control: 'boolean' },
        required: { control: 'boolean' },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof FormInput>;

export const Default: Story = {
    args: {
        label: 'Username',
        placeholder: 'Enter your username',
        value: '',
        onChange: () => { },
    },
};

export const WithValue: Story = {
    args: {
        label: 'Email Address',
        value: 'admiral@synapse.com',
        type: 'email',
        onChange: () => { },
    },
};

export const Required: Story = {
    args: {
        label: 'Password',
        type: 'password',
        required: true,
        placeholder: '••••••••',
        value: '',
        onChange: () => { },
    },
};

export const WithError: Story = {
    args: {
        label: 'API Key',
        value: 'inv_key_123',
        error: 'Invalid API Key format',
        onChange: () => { },
    },
};

export const Disabled: Story = {
    args: {
        label: 'System ID',
        value: 'SYS-001',
        disabled: true,
        onChange: () => { },
    },
};

export const WithMaxLength: Story = {
    args: {
        label: 'Display Name',
        value: 'Neo',
        maxLength: 10,
        placeholder: 'Max 10 chars',
        onChange: () => { },
    },
};
