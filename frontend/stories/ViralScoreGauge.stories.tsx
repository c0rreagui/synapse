import type { Meta, StoryObj } from '@storybook/nextjs';
import { ViralScoreGauge } from '../app/components/oracle/ViralScoreGauge';

const meta: Meta<typeof ViralScoreGauge> = {
    title: 'App/Features/Oracle/ViralScoreGauge',
    component: ViralScoreGauge,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof ViralScoreGauge>;

export const LowScore: Story = {
    args: {
        score: 3.5,
    },
};

export const MediumScore: Story = {
    args: {
        score: 6.8,
    },
};

export const HighScore: Story = {
    args: {
        score: 9.2,
    },
};

export const PerfectScore: Story = {
    args: {
        score: 10,
    },
};
