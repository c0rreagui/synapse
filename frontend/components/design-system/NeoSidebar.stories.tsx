import type { Meta, StoryObj } from '@storybook/react';
import { NeoSidebar } from './NeoSidebar';

// Mock Next.js hook
const mockPathname = '/oracle';

const meta: Meta<typeof NeoSidebar> = {
    title: 'Design System/Organisms/NeoSidebar',
    component: NeoSidebar,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
        nextjs: {
            appDirectory: true,
            navigation: {
                pathname: mockPathname
            }
        }
    },
};

export default meta;
type Story = StoryObj<typeof NeoSidebar>;

export const Default: Story = {
    render: () => (
        <div className="relative min-h-screen w-full bg-[url('https://images.unsplash.com/photo-1534224039826-c7a0eda0e6b3?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
            <NeoSidebar />
        </div>
    )
};
