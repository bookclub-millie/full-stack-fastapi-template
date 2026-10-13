import { Button } from '@kds/ui/components/button'
import { Input } from '@kds/ui/components/input'
import { Eye, EyeOff } from 'lucide-react'
import * as React from 'react'

import { cn } from '@/lib/utils'

interface PasswordInputProps extends React.ComponentProps<'input'> {
  error?: string
}

const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, error, disabled, ...props }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false)

    return (
      <div className="relative">
        <Input
          type={showPassword ? 'text' : 'password'}
          className={cn('min-h-11 pr-12', className)}
          ref={ref}
          disabled={disabled}
          aria-invalid={!!error}
          {...props}
        />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-0 top-0 h-full min-h-11 w-11 text-muted-foreground"
          disabled={disabled}
          onClick={() => setShowPassword(!showPassword)}
          aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
          aria-pressed={showPassword}
        >
          {showPassword ? (
            <EyeOff className="h-4 w-4 text-muted-foreground" />
          ) : (
            <Eye className="h-4 w-4 text-muted-foreground" />
          )}
        </Button>
      </div>
    )
  }
)

PasswordInput.displayName = 'PasswordInput'

export { PasswordInput }
