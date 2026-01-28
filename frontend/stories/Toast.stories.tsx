import type { Meta, StoryObj } from '@storybook/nextjs';
import { Toaster, toast } from 'sonner';
import { NeonButton } from '../app/components/NeonButton';

// Wrapper component to trigger toasts
const ToastDemo = () => {
    return (
        <div className="flex flex-col gap-4 items-start p-8">
            <Toaster position="top-right" theme="dark" richColors />

            <NeonButton variant="primary" onClick={() => toast.success('Operation Successful', { description: 'Data has been synced to the core.' })}>
                Trigger Success
            </NeonButton>

            <NeonButton variant="danger" onClick={() => toast.error('System Failure', { description: 'Critical error in sector 7.' })}>
                Trigger Error
            </NeonButton>

            <NeonButton variant="ghost" onClick={() => toast.info('New Message', { description: 'Incoming transmission from HQ.' })}>
                Trigger Info
            </NeonButton>

            <NeonButton variant="ghost" onClick={() => toast.warning('Low Battery', { description: 'Power levels at 15%.' })}>
                Trigger Warning
            </NeonButton>
        </div>
    );
};

const meta: Meta<typeof ToastDemo> = {
    title: 'App/Molecules/Toast',
    component: ToastDemo,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof ToastDemo>;

export const Interactive: Story = {};
