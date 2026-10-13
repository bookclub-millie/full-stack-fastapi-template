import { defineConfig } from '@playwright/test'

const baseURL = process.env.STORYBOOK_BASE_URL ?? 'http://127.0.0.1:6006'

export default defineConfig({
  testDir: './tests/visual',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 1 : undefined,
  updateSnapshots: 'none',
  snapshotPathTemplate:
    '{testDir}/__screenshots__/{platform}/{projectName}/{testFilePath}/{arg}{ext}',
  outputDir: './visual-test-results',
  reporter: [
    ['list'],
    ['html', { outputFolder: 'visual-report', open: 'never' }]
  ],
  expect: {
    toHaveScreenshot: {
      animations: 'disabled',
      caret: 'hide',
      scale: 'css',
      maxDiffPixels: 0
    }
  },
  use: {
    baseURL,
    browserName: 'chromium',
    deviceScaleFactor: 1,
    locale: 'en-US',
    timezoneId: 'UTC',
    reducedMotion: 'reduce',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'desktop-light',
      use: { viewport: { width: 1280, height: 900 }, colorScheme: 'light' }
    },
    {
      name: 'desktop-dark',
      use: { viewport: { width: 1280, height: 900 }, colorScheme: 'dark' }
    },
    {
      name: 'mobile-light',
      use: { viewport: { width: 390, height: 844 }, colorScheme: 'light' }
    },
    {
      name: 'mobile-dark',
      use: { viewport: { width: 390, height: 844 }, colorScheme: 'dark' }
    }
  ],
  webServer: process.env.STORYBOOK_BASE_URL
    ? undefined
    : {
        command: 'bun run storybook:preview',
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 30_000
      }
})
