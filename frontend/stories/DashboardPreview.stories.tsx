import type { Meta, StoryObj } from '@storybook/react';

const MockDashboard = () => (
    <div className="h-screen w-full bg-[#050505] flex items-center justify-center p-10 animate-in fade-in duration-1000 text-white font-sans">
        <div className="text-center space-y-4">
            <div className="text-6xl mb-4">✨</div>
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">
                System Initialized
            </h1>
            <p className="text-gray-400">Welcome to Synapse Command Center</p>
            <div className="grid grid-cols-3 gap-4 mt-8 max-w-2xl mx-auto">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-32 bg-white/5 rounded-xl border border-white/10" />
                ))}
            </div>
            <div className="mt-8 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-200 text-sm">
                Visual Verification Mode: Animation Engine Bypassed
            </div>
        </div>
    </div>
);

const meta: Meta = {
    title: 'App/Visualization/DashboardPreview',
    component: MockDashboard,
    parameters: {
        layout: 'fullscreen',
    }
};

export default meta;
type Story = StoryObj<typeof MockDashboard>;

export const FinalState: Story = {};
