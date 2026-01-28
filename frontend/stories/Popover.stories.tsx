import type { Meta, StoryObj } from '@storybook/nextjs';
import Popover from '../app/components/Popover';
import { NeonButton } from '../app/components/NeonButton';
import { InformationCircleIcon, CogIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof Popover> = {
    title: 'App/Utilities/Popover',
    component: Popover,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Popover>;

export const Default = {
    render: () => (
        <Popover
            trigger={<NeonButton>Click Options</NeonButton>}
            content={
                <div className="flex flex-col gap-2">
                    <button className="text-left py-2 px-3 hover:bg-white/5 rounded text-white text-sm">Action 1</button>
                    <button className="text-left py-2 px-3 hover:bg-white/5 rounded text-white text-sm">Action 2</button>
                </div>
            }
            title="Menu"
            showClose
        />
    )
};

export const Positions = {
    render: () => (
        <div className="grid grid-cols-2 gap-16">
            <Popover
                position="top"
                trigger={<span className="text-cyan-400 cursor-pointer border-b border-dashed border-cyan-400">Top Popover</span>}
                content={<div className="text-white text-sm">Info appearing on top</div>}
            />
            <Popover
                position="right"
                trigger={<span className="text-purple-400 cursor-pointer border-b border-dashed border-purple-400">Right Popover</span>}
                content={<div className="text-white text-sm">Info appearing on right</div>}
            />
            <Popover
                position="bottom"
                trigger={<span className="text-emerald-400 cursor-pointer border-b border-dashed border-emerald-400">Bottom Popover</span>}
                content={<div className="text-white text-sm">Info appearing on bottom</div>}
            />
            <Popover
                position="left"
                trigger={<span className="text-pink-400 cursor-pointer border-b border-dashed border-pink-400">Left Popover</span>}
                content={<div className="text-white text-sm">Info appearing on left</div>}
            />
        </div>
    )
};
