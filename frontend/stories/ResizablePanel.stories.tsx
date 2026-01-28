import type { Meta, StoryObj } from '@storybook/nextjs';
import ResizablePanel from '../app/components/ResizablePanel';

const meta: Meta<typeof ResizablePanel> = {
    title: 'App/Utilities/ResizablePanel',
    component: ResizablePanel,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="h-screen w-full bg-[#050505]">
                <Story />
            </div>
        )
    ]
};

export default meta;
type Story = StoryObj<typeof ResizablePanel>;

const LeftContent = () => (
    <div className="p-8 h-full bg-slate-900/50">
        <h2 className="text-2xl font-bold text-white mb-4">Editor</h2>
        <div className="space-y-4">
            <div className="h-4 bg-white/5 rounded w-3/4"></div>
            <div className="h-4 bg-white/5 rounded w-1/2"></div>
            <div className="h-4 bg-white/5 rounded w-full"></div>
            <div className="h-4 bg-white/5 rounded w-5/6"></div>
        </div>
    </div>
);

const RightContent = () => (
    <div className="p-8 h-full bg-slate-900/20">
        <h2 className="text-2xl font-bold text-white mb-4">Preview</h2>
        <div className="aspect-video bg-black rounded-lg border border-white/10 flex items-center justify-center text-slate-500">
            Video Preview Area
        </div>
    </div>
);

export const Default: Story = {
    args: {
        left: <LeftContent />,
        right: <RightContent />,
        defaultLeftWidth: 40,
    },
};
