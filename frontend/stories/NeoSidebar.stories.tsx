import type { Meta, StoryObj } from '@storybook/nextjs';
import { NeoSidebar } from '../components/design-system/NeoSidebar';

// Mocking usePathname is handled via parameters if using nextjs addon, 
// or we can wrap it. For now, assuming standard static render.
// Note: In a real Storybook setup for Next.js, we need 'next-router-mock' or similar context.

const meta: Meta<typeof NeoSidebar> = {
    title: 'App/Organisms/NeoSidebar',
    component: NeoSidebar,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
        nextjs: {
            appDirectory: true,
            navigation: {
                pathname: '/',
            },
        },
    },
    decorators: [
        (Story) => (
            <div
                className="flex h-screen bg-[#050505]"
                onClick={(e) => {
                    const target = (e.target as HTMLElement).closest('a');
                    if (target) {
                        e.preventDefault();
                        console.log('Navigation prevented:', target.getAttribute('href'));
                    }
                }}
            >
                <Story />
                <div className="flex-1 ml-[320px] p-8">
                    <h1 className="text-white text-4xl font-bold">Main Content Area</h1>
                    <p className="text-gray-400 mt-4">The sidebar sits fixed on the left.</p>
                    <div className="mt-8 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-yellow-500">
                        <p><strong>Note:</strong> Navigation is disabled in Storybook mode.</p>
                    </div>
                </div>
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof NeoSidebar>;

export const Default: Story = {
    args: {},
};
