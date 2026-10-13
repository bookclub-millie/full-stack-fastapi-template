import { useEffect } from 'react'

import { useTheme } from '@/components/theme-provider'

interface AuthLayoutProps {
  children: React.ReactNode
}

export const AuthLayout = ({ children }: AuthLayoutProps) => {
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    if (theme !== 'light') setTheme('light')
  }, [theme, setTheme])

  return (
    <div
      lang="ko"
      className="flex min-h-svh items-center justify-center bg-muted p-3 text-foreground"
    >
      <div className="grid w-full min-w-0 overflow-hidden rounded-3xl bg-muted lg:min-h-[calc(100svh-1.5rem)] lg:grid-cols-[1.35fr_1fr]">
        <div
          aria-hidden="true"
          className="flex items-center justify-center px-6 py-3 sm:py-5 lg:px-10 lg:py-16"
        >
          <img
            src="/images/selfie-doodle.svg"
            alt=""
            width={1024}
            height={768}
            className="h-32 w-auto max-w-full object-contain sm:h-40 lg:h-auto lg:w-full lg:max-w-xl"
          />
        </div>
        <main className="flex min-w-0 items-center justify-center px-6 py-10 sm:px-12 sm:py-14 lg:rounded-3xl lg:bg-background lg:px-16 lg:py-20">
          <div className="w-full max-w-[400px]">{children}</div>
        </main>
      </div>
    </div>
  )
}
