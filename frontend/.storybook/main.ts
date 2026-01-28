import type { StorybookConfig } from '@storybook/nextjs';
// Trigger rebuild for new dependencies

const config: StorybookConfig = {
  "stories": [
    "../stories/**/*.mdx",
    "../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)",
    "../app/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  "addons": [
    "@storybook/addon-a11y",
    "@storybook/addon-docs"
  ],
  "framework": {
    "name": "@storybook/nextjs",
    "options": {
      "builder": {
        "lazyCompilation": false,
        "fsCache": false
      }
    }
  },
  "typescript": {
    "reactDocgen": "react-docgen"
  },
  "staticDirs": [
    "../public"
  ]
};
export default config;