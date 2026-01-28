import type { Meta, StoryObj } from '@storybook/nextjs';
import ViralSoundPicker, { ViralSound } from '../app/components/ViralSoundPicker';

const mockSounds: ViralSound[] = [
    {
        id: '1',
        title: 'Cyberpunk Lo-Fi',
        author: 'Synapse Beats',
        cover_url: '',
        preview_url: 'https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
        duration: 30,
        usage_count: 15400,
        category: 'Tech',
        viral_score: 95,
        status: 'exploding',
        niche: 'tech',
        growth_rate: 150
    },
    {
        id: '2',
        title: 'Gym Phonk 2024',
        author: 'Fitness Hub',
        cover_url: '',
        preview_url: '',
        duration: 15,
        usage_count: 890000,
        category: 'Fitness',
        viral_score: 88,
        status: 'rising',
        niche: 'fitness',
        growth_rate: 45
    },
    {
        id: '3',
        title: 'Generic Pop Song',
        author: 'Pop Star',
        cover_url: '',
        preview_url: '',
        duration: 60,
        usage_count: 5000,
        category: 'General',
        viral_score: 40,
        status: 'normal',
        niche: 'lifestyle',
        growth_rate: 0
    }
];

// Mock Fetch Global
const mockFetch = (url: string): Promise<any> => {
    return new Promise((resolve) => {
        if (url.includes('/api/v1/viral-sounds/trending')) {
            resolve({
                ok: true,
                json: async () => ({ sounds: mockSounds })
            });
            return;
        }
        if (url.includes('/api/v1/viral-sounds/search')) {
            resolve({
                ok: true,
                json: async () => ({ sounds: [mockSounds[0]] }) // Simulate search result
            });
            return;
        }
        resolve({ ok: false });
    });
};

const meta: Meta<typeof ViralSoundPicker> = {
    title: 'App/Organisms/ViralSoundPicker',
    component: ViralSoundPicker,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => {
            // @ts-ignore
            global.fetch = mockFetch;
            return (
                <div className="h-screen w-full flex items-center justify-center bg-gray-900 p-8">
                    <Story />
                </div>
            )
        },
    ],
};

export default meta;
type Story = StoryObj<typeof ViralSoundPicker>;

export const Default: Story = {
    args: {
        isOpen: true,
        onClose: () => console.log('Close clicked'),
        onSelect: (sound) => console.log('Selected:', sound),
        initialCategory: 'all',
    },
};

export const WithCategory: Story = {
    args: {
        isOpen: true,
        onClose: () => { },
        onSelect: () => { },
        initialCategory: 'Dance',
    },
};
