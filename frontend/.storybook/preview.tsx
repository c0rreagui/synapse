import "../app/globals.css";
import type { Preview } from '@storybook/nextjs'
import { MoodProvider } from '../app/context/MoodContext';

const preview: Preview = {
  parameters: {
    nextjs: {
      appDirectory: true,
    },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        { name: 'dark', value: '#05040a' },
        { name: 'light', value: '#ffffff' },
      ],
    },
  },
  decorators: [
    (Story) => (
      <MoodProvider>
      <Story />
      </MoodProvider>
    ),
  ],
};

export default preview;