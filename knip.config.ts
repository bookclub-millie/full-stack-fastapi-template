import type { KnipConfig } from 'knip'

const config: KnipConfig = {
  workspaces: {
    '.': {
      entry: [],
      project: ['*.{ts,css}']
    },
    frontend: {
      entry: [
        // Generated SDK and vendored UI primitives are reusable public surfaces.
        'src/client/index.ts',
        'src/components/ui/**/*.{ts,tsx}',
        // Setup projects and shared fixture factories are invoked by test tooling.
        'tests/e2e/auth.setup.ts',
        'tests/e2e/utils/random.ts'
      ],
      project: [
        'src/**/*.{ts,tsx,css,mdx}',
        'tests/**/*.ts',
        '.storybook/**/*.{ts,tsx}',
        '*.ts'
      ],
      ignore: ['src/client/**'],
      playwright: {
        config: ['playwright.config.ts', 'playwright.visual.config.ts']
      },
      vitest: {
        config: ['vitest.config.ts', '.storybook/vitest.config.ts']
      }
    },
    'packages/ui': {
      // Exported subpaths are the package's component API, even before app use.
      entry: ['src/components/*.tsx', 'src/hooks/*.ts', 'src/lib/*.ts'],
      project: ['src/**/*.{ts,tsx,css}', '*.mjs']
    },
    'packages/react-email': {
      entry: ['emails/**/*.tsx'],
      project: ['emails/**/*.tsx', 'ui/**/*.{tsx,css}']
    }
  },
  // Tailwind's CSS imports are real dependencies, not JavaScript imports.
  compilers: {
    css: (text: string) => [...text.matchAll(/(?<=@)import[^;]+/gu)].join('\n')
  }
}

export default config
