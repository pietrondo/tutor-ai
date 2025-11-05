const js = require('@eslint/js')
const nextPlugin = require('@next/eslint-plugin-next')
const tsPlugin = require('@typescript-eslint/eslint-plugin')
const tsParser = require('@typescript-eslint/parser')
const path = require('path')
const globals = require('globals')

module.exports = [
  {
    ignores: ['.next/**', 'node_modules/**', 'coverage/**', 'dist/**'],
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      ecmaVersion: 2022,
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      '@next/next': nextPlugin,
    },
    rules: {
      ...nextPlugin.configs['core-web-vitals'].rules,
    },
  },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: path.join(__dirname, 'tsconfig.json'),
        tsconfigRootDir: __dirname,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      '@typescript-eslint/explicit-module-boundary-types': 'off',
    },
  },
  {
    files: ['**/__tests__/**/*.{js,jsx,ts,tsx}', '**/*.test.{js,jsx,ts,tsx}', '**/*.spec.{js,jsx,ts,tsx}', 'jest.setup.js'],
    languageOptions: {
      globals: {
        ...globals.jest,
      },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/require-await': 'off',
    },
  },
]
