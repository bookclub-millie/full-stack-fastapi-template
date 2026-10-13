import { Button } from "@kds/ui/components/button"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "@/components/theme-provider"

export function ThemeModeToggle() {
  const { setTheme, resolvedTheme } = useTheme()
  const isDark = resolvedTheme === "dark"
  const label = isDark
    ? "현재 다크 모드. 라이트 모드로 전환"
    : "현재 라이트 모드. 다크 모드로 전환"

  return (
    <Button
      aria-label={label}
      aria-pressed={isDark}
      className="relative"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      size="icon"
      title={label}
      variant="outline"
    >
      <Sun
        aria-hidden="true"
        className="size-4 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90"
      />
      <Moon
        aria-hidden="true"
        className="absolute size-4 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0"
      />
    </Button>
  )
}
