import { TooltipProvider } from '@kds/ui/components/tooltip'
import type { Preview } from '@storybook/react-vite'
import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { ThemeProvider, useTheme } from '../src/components/theme-provider'
import '../src/index.css'

const ThemeSync = ({
  theme,
  children
}: {
  theme: 'light' | 'dark'
  children: ReactNode
}) => {
  const { theme: currentTheme, setTheme } = useTheme()
  useEffect(() => {
    document.documentElement.lang = 'ko'
    if (currentTheme !== theme) setTheme(theme)
  }, [currentTheme, theme, setTheme])
  return <>{children}</>
}

const preview: Preview = {
  tags: ['autodocs'],
  globalTypes: {
    theme: {
      description: 'KDS color mode',
      toolbar: {
        icon: 'paintbrush',
        items: ['light', 'dark'],
        dynamicTitle: true
      }
    }
  },
  initialGlobals: {
    theme: window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'
  },
  parameters: {
    layout: 'padded',
    a11y: { test: 'error' },
    controls: { expanded: true }
  },
  decorators: [
    (Story, context) => (
      <ThemeProvider defaultTheme="light" storageKey="storybook-kds-theme">
        <ThemeSync theme={context.globals.theme === 'dark' ? 'dark' : 'light'}>
          <TooltipProvider>
            <main
              className="mx-auto w-full max-w-3xl text-foreground"
              lang="ko"
            >
              <Story />
            </main>
          </TooltipProvider>
        </ThemeSync>
      </ThemeProvider>
    )
  ]
}

export default preview
