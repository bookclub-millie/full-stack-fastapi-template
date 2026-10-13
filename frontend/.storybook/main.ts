import { fileURLToPath } from 'node:url'
import type { StorybookConfig } from '@storybook/react-vite'
import tailwindcss from '@tailwindcss/vite'
import { mergeConfig } from 'vite'

const config: StorybookConfig = {
  stories: ['../src/stories/**/*.stories.tsx'],
  addons: [
    '@storybook/addon-docs',
    '@storybook/addon-a11y',
    '@storybook/addon-vitest'
  ],
  framework: '@storybook/react-vite',
  core: {
    builder: {
      name: '@storybook/builder-vite',
      options: {
        viteConfigPath: fileURLToPath(
          new URL('./vite.config.ts', import.meta.url)
        )
      }
    },
    disableTelemetry: true
  },
  staticDirs: ['../public'],
  viteFinal(config) {
    return mergeConfig(config, {
      plugins: [tailwindcss()],
      resolve: {
        alias: { '@': fileURLToPath(new URL('../src', import.meta.url)) }
      }
    })
  }
}

export default config
