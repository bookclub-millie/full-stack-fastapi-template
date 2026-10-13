import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@kds/ui/components/button'
import { Input } from '@kds/ui/components/input'
import {
  createFileRoute,
  Link as RouterLink,
  redirect
} from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import type { Body_login_login_access_token as AccessToken } from '@/client'
import { AuthLayout } from '@/components/Common/auth-layout'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form'
import { PasswordInput } from '@/components/ui/password-input'
import useAuth, { isLoggedIn } from '@/hooks/use-auth'

const formSchema = z.object({
  username: z.email({ message: '이메일 주소 형식을 확인해 주세요.' }),
  password: z
    .string()
    .min(1, { message: '비밀번호를 입력해 주세요.' })
    .min(8, { message: '비밀번호는 8자 이상 입력해 주세요.' })
}) satisfies z.ZodType<AccessToken>

type FormData = z.infer<typeof formSchema>

const Login = () => {
  const { loginMutation } = useAuth()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: 'onBlur',
    criteriaMode: 'all',
    defaultValues: {
      username: '',
      password: ''
    }
  })

  const onSubmit = (data: FormData) => {
    if (loginMutation.isPending) return
    loginMutation.mutate(data)
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
              다시 만나 반가워요!
            </h1>
          </div>
          <div className="grid gap-6">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>이메일</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder="name@example.com"
                      type="email"
                      autoComplete="username"
                      autoCapitalize="none"
                      spellCheck={false}
                      className="h-12 px-4 md:text-base"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>비밀번호</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder="비밀번호 입력"
                      autoComplete="current-password"
                      className="h-12 px-4 pr-12 md:text-base"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <RouterLink
              to="/recover-password"
              className="inline-flex min-h-11 items-center justify-self-end rounded-md text-sm underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              비밀번호 찾기
            </RouterLink>
            <Button
              type="submit"
              className="h-12 w-full bg-foreground text-base text-background hover:bg-foreground/90"
              disabled={loginMutation.isPending}
              aria-busy={loginMutation.isPending}
            >
              {loginMutation.isPending && (
                <Loader2
                  aria-hidden="true"
                  className="size-4 animate-spin motion-reduce:animate-none"
                />
              )}
              로그인
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            아직 계정이 없나요?{' '}
            <RouterLink
              to="/signup"
              className="inline-flex min-h-11 items-center rounded-md px-1 font-medium text-foreground underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              회원가입
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
export const Route = createFileRoute('/login')({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: '/'
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: '로그인'
      }
    ]
  })
})
