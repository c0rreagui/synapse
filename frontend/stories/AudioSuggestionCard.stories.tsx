import type { Meta, StoryObj } from '@storybook/nextjs';
import AudioSuggestionCard, { AudioSuggestion } from '../app/components/AudioSuggestionCard';

const MOCK_SUGGESTION: AudioSuggestion = {
    sound_id: '123',
    title: 'Neon Nights',
    author: 'CyberPunk Beats',
    viral_score: 95,
    reason: 'exploding',
    confidence: 0.92,
    niche: 'tech',
    status: 'exploding',
    usage_count: 54200,
    cover_url: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&q=80&w=200', // Music/Mic image
    preview_url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3', // Mock audio
};

const meta: Meta<typeof AudioSuggestionCard> = {
    title: 'App/Molecules/AudioSuggestionCard',
    component: AudioSuggestionCard,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[450px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof AudioSuggestionCard>;

export const Default: Story = {
    args: {
        suggestion: MOCK_SUGGESTION,
    },
};

export const Compact: Story = {
    args: {
        suggestion: MOCK_SUGGESTION,
        compact: true,
    },
};

export const Trending: Story = {
    args: {
        suggestion: {
            ...MOCK_SUGGESTION,
            title: 'Morning Vibes',
            author: 'LoFi Girl',
            viral_score: 75,
            reason: 'trending',
            status: 'rising',
            usage_count: 12000,
            cover_url: '', // Test empty cover
        },
    },
};

export const NicheMatch: Story = {
    args: {
        suggestion: {
            ...MOCK_SUGGESTION,
            title: 'Gym Hardstyle',
            author: 'FitnessPro',
            viral_score: 88,
            reason: 'niche_match',
            status: 'stable',
            usage_count: 3200,
        },
    },
};
