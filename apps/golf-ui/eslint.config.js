import tseslint from 'typescript-eslint';
import eslintPluginReact from 'eslint-plugin-react';
import eslintPluginReactHooks from 'eslint-plugin-react-hooks';
import jsxA11y from 'eslint-plugin-jsx-a11y';

const reactRecommendedRules = eslintPluginReact.configs?.recommended?.rules ?? {};
const jsxA11yRecommendedRules = jsxA11y.configs?.recommended?.rules ?? {};
const tsRecommendedRules = (tseslint.configs?.recommended ?? []).reduce(
  (rules, config) => ({ ...rules, ...(config.rules ?? {}) }),
  {}
);

export default [
  {
    ignores: ['dist', 'node_modules', 'coverage', 'public'],
  },
  {
    files: ['src/**/*.{ts,tsx}', 'tests/**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        project: './tsconfig.json',
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
      react: eslintPluginReact,
      'react-hooks': eslintPluginReactHooks,
      'jsx-a11y': jsxA11y,
    },
    rules: {
      ...tsRecommendedRules,
      ...reactRecommendedRules,
      ...jsxA11yRecommendedRules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
];
