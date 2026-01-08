import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // Custom rules - Suppress warnings for intentional design decisions
  {
    rules: {
      // Disable inline styles warning - we use them intentionally for dynamic styling
      "@next/next/no-inline-styles": "off",
      "react/no-inline-styles": "off",

      // Disable accessibility warnings that conflict with our component design
      "jsx-a11y/label-has-associated-control": "off",
      "jsx-a11y/click-events-have-key-events": "off",
      "jsx-a11y/no-static-element-interactions": "off",
      "jsx-a11y/anchor-is-valid": "off",

      // Allow unused variables prefixed with underscore
      "@typescript-eslint/no-unused-vars": ["warn", {
        "argsIgnorePattern": "^_",
        "varsIgnorePattern": "^_"
      }],

      // Disable warnings for empty functions (common in event handlers)
      "@typescript-eslint/no-empty-function": "off",

      // Allow any type in specific cases
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
]);

export default eslintConfig;
