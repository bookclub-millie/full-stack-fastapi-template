import { fileURLToPath } from 'node:url'
import { storybookTest } from '@storybook/addon-vitest/vitest-plugin'
import { playwright } from '@vitest/browser-playwright'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [
    storybookTest({ configDir: fileURLToPath(new URL('.', import.meta.url)) })
  ],
  test: {
    name: 'storybook',
    reporters: ['default', 'junit'],
    outputFile: { junit: 'test-results/storybook.xml' },
    browser: {
      enabled: true,
      headless: true,
      instances: [
        {
          browser: 'chromium',
          name: 'storybook-light',
          provider: playwright({ contextOptions: { colorScheme: 'light' } })
        },
        {
          browser: 'chromium',
          name: 'storybook-dark',
          provider: playwright({ contextOptions: { colorScheme: 'dark' } })
        }
      ]
    }
  }
})
