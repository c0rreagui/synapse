import type { Meta, StoryObj } from '@storybook/nextjs';
import Breadcrumb from '../app/components/Breadcrumb';
import { UserIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof Breadcrumb> = {
    title: 'App/Molecules/Breadcrumb',
    component: Breadcrumb,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div onClick={(e) => {
                const target = (e.target as HTMLElement).closest('a');
                if (target) {
                    e.preventDefault();
                    console.log('Breadcrumb navigation prevented:', target.getAttribute('href'));
                }
            }}>
                <Story />
            </div>
        )
    ]
};

export default meta;
type Story = StoryObj<typeof Breadcrumb>;

export const Default: Story = {
    args: {
        items: [
            { label: 'Users', href: '/users' },
            { label: 'Alice', href: '/users/alice' },
            { label: 'Settings' },
        ],
    },
};

export const WithIcons: Story = {
    args: {
        items: [
            { label: 'Profiles', href: '/profiles', icon: <UserIcon className="w-3 h-3" /> },
            { label: 'Edit Profile' },
        ],
    },
};
