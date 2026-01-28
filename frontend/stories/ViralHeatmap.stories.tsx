import type { Meta, StoryObj } from '@storybook/nextjs';
import ViralHeatmap from '../app/components/analytics/ViralHeatmap';

const meta: Meta<typeof ViralHeatmap> = {
    title: 'App/Features/Analytics/ViralHeatmap',
    component: ViralHeatmap,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[600px] h-[300px] bg-black/50 p-4 rounded-xl">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof ViralHeatmap>;

const generateData = () => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const data = [];
    for (let d = 0; d < 7; d++) {
        for (let h = 0; h < 24; h++) {
            // Simulate viral peak at 18:00 - 21:00 on weekends
            const isWeekend = d >= 5;
            const isPrimeTime = h >= 18 && h <= 21;
            const base = isWeekend && isPrimeTime ? 80 : 20;
            const value = Math.floor(Math.random() * 50) + base;

            data.push({
                day: days[d],
                day_index: d === 6 ? 0 : d + 1, // Python style ish
                hour: h,
                value: value,
                count: value * 10
            });
        }
    }
    return data;
};

export const Default: Story = {
    args: {
        data: generateData(),
    },
};

export const NoData: Story = {
    args: {
        data: [],
    },
};
