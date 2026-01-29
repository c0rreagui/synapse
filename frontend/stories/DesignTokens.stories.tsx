import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta = {
    title: 'Design System/Tokens',
    parameters: {
        layout: 'fullscreen',
    },
};

export default meta;
type Story = StoryObj;

// Color Palette Definition
const colors = {
    core: [
        { name: 'Deep Void', value: '#05040a', class: 'bg-black/90' },
        { name: 'Neural Layer', value: '#0f0a15', class: 'bg-gray-900' },
        { name: 'Glass Module', value: 'rgba(13, 17, 23, 0.7)', class: 'bg-gray-800/70' },
        { name: 'Border', value: 'rgba(139, 92, 246, 0.2)', class: 'border-violet-500/20' },
    ],
    accents: [
        { name: 'Primary Violet', value: '#8b5cf6', class: 'bg-violet-500' },
        { name: 'Secondary Magenta', value: '#d946ef', class: 'bg-fuchsia-500' },
        { name: 'Cyan', value: '#06b6d4', class: 'bg-cyan-500' },
    ],
    semantic: [
        { name: 'Success', value: '#10b981', class: 'bg-emerald-500' },
        { name: 'Error', value: '#fb7185', class: 'bg-rose-400' },
        { name: 'Warning', value: '#f59e0b', class: 'bg-amber-500' },
    ],
};

const ColorSwatch = ({ name, value, className }: { name: string; value: string; className?: string }) => (
    <div className="flex flex-col gap-2">
        <div
            className={`h-24 w-full rounded-xl border border-white/10 shadow-lg ${className}`}
            style={{ backgroundColor: !className?.includes('bg-') ? value : undefined }}
        >
            {/* Visual representation */}
        </div>
        <div className="space-y-1">
            <p className="font-medium text-white/90 text-sm">{name}</p>
            <p className="font-mono text-xs text-white/50">{value}</p>
        </div>
    </div>
);

export const Colors: Story = {
    render: () => (
        <div className="min-h-screen bg-[#05040a] p-12 text-white">
            <div className="max-w-6xl mx-auto space-y-16">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent mb-4">
                        Neo-Glass Palette
                    </h1>
                    <p className="text-white/60 text-lg">
                        Core colors and semantic values defining the Synapse interface.
                    </p>
                </div>

                <section className="space-y-6">
                    <h2 className="text-xl font-semibold border-b border-white/10 pb-2">Core Foundations</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {colors.core.map((c) => (
                            <ColorSwatch key={c.name} {...c} className={c.class} />
                        ))}
                    </div>
                </section>

                <section className="space-y-6">
                    <h2 className="text-xl font-semibold border-b border-white/10 pb-2">Neon Accents</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {colors.accents.map((c) => (
                            <ColorSwatch key={c.name} {...c} className={c.class} />
                        ))}
                    </div>
                </section>

                <section className="space-y-6">
                    <h2 className="text-xl font-semibold border-b border-white/10 pb-2">Semantic States</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {colors.semantic.map((c) => (
                            <ColorSwatch key={c.name} {...c} className={c.class} />
                        ))}
                    </div>
                </section>
            </div>
        </div>
    ),
};

export const Typography: Story = {
    render: () => (
        <div className="min-h-screen bg-[#05040a] p-12 text-white">
            <div className="max-w-6xl mx-auto space-y-16">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-4">
                        Typography
                    </h1>
                    <p className="text-white/60 text-lg">
                        Inter for UI, JetBrains Mono for code.
                    </p>
                </div>

                <div className="grid gap-12">
                    <div className="space-y-4">
                        <span className="text-xs font-mono text-white/40">Display / 4XL</span>
                        <p className="text-4xl font-bold">The quick brown fox</p>
                    </div>
                    <div className="space-y-4">
                        <span className="text-xs font-mono text-white/40">Heading / 2XL</span>
                        <p className="text-2xl font-semibold">Jumps over the lazy dog</p>
                    </div>
                    <div className="space-y-4">
                        <span className="text-xs font-mono text-white/40">Body / Base</span>
                        <p className="text-base text-white/80">
                            Synapse interface text aims for maximum legibility with high contrast
                            against dark glass backgrounds.
                        </p>
                    </div>
                    <div className="space-y-4">
                        <span className="text-xs font-mono text-white/40">Monospace / Sm</span>
                        <p className="font-mono text-sm text-cyan-400">
                            const system = "ready"; // awaiting input
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
};

export const Effects: Story = {
    render: () => (
        <div className="min-h-screen bg-[#05040a] p-12 text-white">
            <div className="max-w-6xl mx-auto space-y-16">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent mb-4">
                        Visual Effects
                    </h1>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    <div className="p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl">
                        <h3 className="text-lg font-medium mb-2">Glass Panel</h3>
                        <p className="text-sm text-white/60">Standard backdrop blur with subtle border.</p>
                    </div>

                    <div className="p-8 rounded-2xl border border-violet-500/50 bg-violet-500/5 shadow-[0_0_30px_-5px_rgba(139,92,246,0.3)]">
                        <h3 className="text-lg font-medium mb-2 text-violet-300">Neon Glow</h3>
                        <p className="text-sm text-white/60">Active state indication.</p>
                    </div>

                    <div className="p-8 rounded-[2rem] border border-white/10 bg-white/5">
                        <h3 className="text-lg font-medium mb-2">Squircle</h3>
                        <p className="text-sm text-white/60">Super-ellipse geometry for organic feel.</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
