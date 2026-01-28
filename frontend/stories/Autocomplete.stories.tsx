import type { Meta, StoryObj } from '@storybook/nextjs';
import Autocomplete from '../app/components/Autocomplete';
import { useState } from 'react';

const meta: Meta<typeof Autocomplete> = {
    title: 'App/Utilities/Autocomplete',
    component: Autocomplete,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => <div className="h-64"><Story /></div> // Space for dropdown
    ]
};

export default meta;
type Story = StoryObj<typeof Autocomplete>;

const frameworks = [
    'React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Nuxt', 'Remix', 'Astro',
    'Solid', 'Qwik', 'Preact', 'Ember', 'Gatsby', 'Alpine', 'Lit'
];

export const Interactive = {
    render: () => {
        const [value, setValue] = useState('');
        return (
            <div className="w-80">
                <Autocomplete
                    label="Choose Framework"
                    value={value}
                    onChange={setValue}
                    suggestions={frameworks}
                    placeholder="Type framework name..."
                />
            </div>
        );
    }
};

export const PreFilled: Story = {
    args: {
        label: 'Favorite Tech',
        value: 'React',
        suggestions: frameworks,
        placeholder: 'Search...',
    },
};
