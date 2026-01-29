import type { Meta, StoryObj } from '@storybook/nextjs';
import * as LucideIcons from 'lucide-react';
import { useState } from 'react';

const IconGrid = ({ icons }: { icons: Record<string, any> }) => {
    const [filter, setFilter] = useState('');
    const [copied, setCopied] = useState<string | null>(null);

    // Filter out non-component exports if any (though lucide-react mostly exports components)
    // and apply search filter
    const filteredIcons = Object.entries(icons).filter(([name, Icon]) => {
        // Filter out non-component exports like 'createLucideIcon', 'icons', 'default'
        // Lucide icons are PascalCase
        const isPascalCase = /^[A-Z]/.test(name);
        // 'Icon' is the generic component export which fails without props
        if (!isPascalCase || name === 'Icon') return false;

        const matchesFilter = name.toLowerCase().includes(filter.toLowerCase());
        return matchesFilter;
    });

    const handleCopy = (name: string) => {
        const text = `import { ${name} } from 'lucide-react';`;
        navigator.clipboard.writeText(text);
        setCopied(name);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <div className="p-8 bg-[#050507] min-h-screen text-gray-300">
            <div className="mb-8 space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Lucide Icons</h1>
                        <p className="text-gray-500">
                            {filteredIcons.length} icons found. Click to copy import.
                        </p>
                    </div>
                    <input
                        type="text"
                        placeholder="Search icons..."
                        className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500 transition-colors w-64"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-4">
                {filteredIcons.map(([name, Icon]) => (
                    <button
                        key={name}
                        onClick={() => handleCopy(name)}
                        className="group flex flex-col items-center justify-center p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-purple-500/10 hover:border-purple-500/50 hover:scale-105 transition-all duration-200 relative"
                    >
                        {/* Lucide icons render as components */}
                        <Icon className={`w-8 h-8 mb-3 transition-colors ${copied === name ? 'text-emerald-400' : 'text-gray-400 group-hover:text-white'}`} strokeWidth={1.5} />
                        <span className="text-[10px] text-center text-gray-500 font-mono break-all group-hover:text-purple-300">
                            {name}
                        </span>

                        {copied === name && (
                            <div className="absolute inset-0 bg-emerald-500/10 rounded-xl flex items-center justify-center backdrop-blur-sm">
                                <span className="text-xs font-bold text-emerald-400 bg-black/50 px-2 py-1 rounded">COPIED!</span>
                            </div>
                        )}
                    </button>
                ))}
            </div>

            {filteredIcons.length === 0 && (
                <div className="text-center py-20 text-gray-600">
                    No icons found matching "{filter}"
                </div>
            )}
        </div>
    );
};

const meta: Meta = {
    title: 'App/Foundation/Iconography',
    component: IconGrid,
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof IconGrid>;

export const Library: Story = {
    args: {
        icons: LucideIcons,
    },
    parameters: {
        docs: {
            description: {
                story: 'Complete Lucide React icon library.'
            }
        }
    }
};
