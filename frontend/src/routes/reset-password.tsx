import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@kds/ui/components/button'
import { useMutation } from '@tanstack/react-query'
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
  useNavigate
} from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { LoginService } from '@/client'
import { AuthLayout } from '@/components/common/auth-layout'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form'
import { PasswordInput } from '@/components/ui/password-input'
import { isLoggedIn, showAuthError } from '@/hooks/use-auth'

const searchSchema = z.object({
  token: z.string().catch('')
})

const formSchema = z
  .object({
    new_password: z
      .string()
      .min(1, { message: '비밀번호를 입력해 주세요.' })
      .min(8, { message: '비밀번호는 8자 이상 입력해 주세요.' }),
    confirm_password: z
      .string()
      .min(1, { message: '비밀번호를 한 번 더 입력해 주세요.' })
  })
  .refine(data => data.new_password === data.confirm_password, {
    message: '비밀번호가 일치하지 않아요. 다시 확인해 주세요.',
    path: ['confirm_password']
  })

type FormData = z.infer<typeof formSchema>

const ResetPassword = () => {
  const { token } = Route.useSearch()
  const navigate = useNavigate()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: 'onBlur',
    criteriaMode: 'all',
    defaultValues: {
      new_password: '',
      confirm_password: ''
    }
  })

  const mutation = useMutation({
    mutationFn: (data: { new_password: string; token: string }) =>
      LoginService.resetPassword({ body: data }),
    onSuccess: () => {
      toast.success('비밀번호를 바꿨어요.', {
        description: '새 비밀번호로 로그인해 주세요.'
      })
      form.reset()
      navigate({ to: '/login' })
    },
    onError: showAuthError
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate({ new_password: data.new_password, token })
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          noValidate
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-8 sm:gap-10"
        >
          <div className="space-y-3 text-center">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              비밀번호 재설정
            </h1>
            <p className="break-keep text-sm text-muted-foreground sm:text-base">
              새로 사용할 비밀번호를 입력해 주세요.
            </p>
          </div>

          <div className="grid gap-6">
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>새 비밀번호</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="new-password-input"
                      placeholder="8자 이상"
                      autoComplete="new-password"
                      className="h-12 px-4 pr-12 md:text-base"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>비밀번호 확인</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="confirm-password-input"
                      placeholder="비밀번호 한 번 더 입력"
                      autoComplete="new-password"
                      className="h-12 px-4 pr-12 md:text-base"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button
              type="submit"
              className="h-12 w-full bg-foreground text-base text-background hover:bg-foreground/90"
              disabled={mutation.isPending}
              aria-busy={mutation.isPending}
            >
              {mutation.isPending && (
                <Loader2
                  aria-hidden="true"
                  className="size-4 animate-spin motion-reduce:animate-none"
                />
              )}
              비밀번호 재설정
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            비밀번호가 기억났나요?{' '}
            <RouterLink
              to="/login"
              className="inline-flex min-h-11 items-center rounded-md px-1 font-medium text-foreground underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              로그인
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
export const Route = createFileRoute('/reset-password')({
  component: ResetPassword,
  validateSearch: searchSchema,
  beforeLoad: async ({ search }) => {
    if (isLoggedIn()) {
      throw redirect({ to: '/' })
    }
    if (!search.token) {
      throw redirect({ to: '/login' })
    }
  },
  head: () => ({
    meta: [
      {
        title: '비밀번호 재설정'
      }
    ]
  })
})
