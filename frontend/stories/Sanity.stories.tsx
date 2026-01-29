import type { Meta, StoryObj } from '@storybook/nextjs';

const SanityCheck = () => (
    <div style={{ color: '#0f0', padding: 20, background: '#111' }}>
        <h1>SYSTEM ONLINE</h1>
        <p>If you see this, Storybook is working.</p>
    </div>
);

const meta: Meta<typeof SanityCheck> = {
    title: 'Debug/SanityCheck',
    component: SanityCheck,
    parameters: {
        layout: 'centered',
    },
};

export default meta;
type Story = StoryObj<typeof SanityCheck>;

export const Working: Story = {};
