import type { Meta, StoryObj } from '@storybook/nextjs';
import { SentimentCard } from '../app/components/oracle/SentimentCard';

const meta: Meta<typeof SentimentCard> = {
    title: 'App/Features/Oracle/SentimentCard',
    component: SentimentCard,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[700px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof SentimentCard>;

export const Positive: Story = {
    args: {
        data: {
            score: 87,
            dominant_emotion: 'Excitement',
            top_questions: ['How do I get early access?', 'Is this compatible with Mac?', 'What is the pricing?'],
            lovers: [],
            haters: [],
            debate_topic: 'AI Ethics vs Efficiency',
        },
    },
};

export const Negative: Story = {
    args: {
        data: {
            score: 34,
            dominant_emotion: 'Frustration',
            top_questions: ['Why is the server down?', 'Refund policy?', 'Bug in login'],
            lovers: [],
            haters: [],
            debate_topic: 'Downtime Compensation',
        },
    },
};

export const Neutral: Story = {
    args: {
        data: {
            score: 52,
            dominant_emotion: 'Curiosity',
            top_questions: ['What does this update do?', 'Any new features?', 'Docs link?'],
            lovers: [],
            haters: [],
        },
    },
};
