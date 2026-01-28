import type { Meta, StoryObj } from '@storybook/nextjs';
import Tooltip from '../app/components/Tooltip';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof Tooltip> = {
    title: 'App/Atoms/Tooltip',
    component: Tooltip,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Tooltip>;

export const Default: Story = {
    args: {
        content: 'This is a helpful tip',
        children: <button className="text-white bg-blue-600 px-4 py-2 rounded">Hover Me</button>,
    },
};

export const WithShortcut: Story = {
    args: {
        content: 'Save Changes',
        shortcut: 'Ctrl+S',
        position: 'right',
        children: <button className="text-white bg-green-600 px-4 py-2 rounded">Save</button>,
        delay: 0,
    },
};

export const IconTrigger: Story = {
    args: {
        content: 'More Info',
        position: 'top',
        children: <InformationCircleIcon className="w-6 h-6 text-gray-400 hover:text-white" />,
    },
};
