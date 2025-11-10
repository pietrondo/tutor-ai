const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(react-markdown|remark-gfm|micromark|mdast-util-.*|unist-util-.*|hast-util-.*|vfile|bail|is-plain-obj|trough|is-decimal|is-hexadecimal|is-alphanumerical|is-alphabetical|decode-named-character-reference|character-entities|character-entities-legacy|parse-entities|character-reference-invalid|ccount|longest-streak|trim-lines|space-separated-tokens|locate|markdown-table|comma-separated-tokens|zwitch|escape-string-regexp|unist-util-is|unist-util-stringify-position|unist-util-position|unist-util-generated|unist-util-visit-parents|unist-util-visit|mdast-util-to-hast|mdast-util-to-markdown|mdast-util-phrasing|mdast-util-to-string|mdast-util-define|mdast-util-find-and-replace|mdast-util-from-markdown|mdast-util-gfm|mdast-util-gfm-autolink-literal|mdast-util-gfm-footnote|mdast-util-gfm-strikethrough|mdast-util-gfm-table|mdast-util-gfm-task-list-item|micromark-extension-gfm-autolink-literal|micromark-extension-gfm-footnote|micromark-extension-gfm-strikethrough|micromark-extension-gfm-table|micromark-extension-gfm-task-list-item|micromark-extension-gfm|micromark-util-combine-extensions|micromark-util-character|micromark-util-chunked|micromark-util-classify-character|micromark-util-code|micromark-util-decode-numeric-character-reference|micromark-util-decode-string|micromark-util-encode|micromark-util-events-to-acorn|micromark-util-html-tag-name|micromark-util-normalize-identifier|micromark-util-parse|micromark-util-resolve-all|micromark-util-sanitize-uri|micromark-util-subtokenize|micromark-util-symbol|micromark-util-types|micromark-util-warning|micromark)/)'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!**/node_modules/**',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
