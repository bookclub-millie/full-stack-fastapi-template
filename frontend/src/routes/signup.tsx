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

const formSchema = z
  .object({
    email: z.email({ message: '이메일 주소 형식을 확인해 주세요.' }),
    full_name: z.string().min(1, { message: '이름을 입력해 주세요.' }),
    password: z
      .string()
      .min(1, { message: '비밀번호를 입력해 주세요.' })
      .min(8, { message: '비밀번호는 8자 이상 입력해 주세요.' }),
    confirm_password: z
      .string()
      .min(1, { message: '비밀번호를 한 번 더 입력해 주세요.' })
  })
  .refine(data => data.password === data.confirm_password, {
    message: '비밀번호가 일치하지 않아요. 다시 확인해 주세요.',
    path: ['confirm_password']
  })

type FormData = z.infer<typeof formSchema>

const SignUp = () => {
  const { signUpMutation } = useAuth()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: 'onBlur',
    criteriaMode: 'all',
    defaultValues: {
      email: '',
      full_name: '',
      password: '',
      confirm_password: ''
    }
  })

  const onSubmit = (data: FormData) => {
    if (signUpMutation.isPending) return

    // exclude confirm_password from submission data
    const { confirm_password: _confirm_password, ...submitData } = data
    signUpMutation.mutate(submitData)
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
              계정 만들기
            </h1>
          </div>
          <div className="grid gap-6">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>이름</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="full-name-input"
                      placeholder="이름 입력"
                      type="text"
                      autoComplete="name"
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
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>이메일</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder="name@example.com"
                      type="email"
                      autoComplete="email"
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
              disabled={signUpMutation.isPending}
              aria-busy={signUpMutation.isPending}
            >
              {signUpMutation.isPending && (
                <Loader2
                  aria-hidden="true"
                  className="size-4 animate-spin motion-reduce:animate-none"
                />
              )}
              회원가입
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            이미 계정이 있나요?{' '}
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
export const Route = createFileRoute('/signup')({
  component: SignUp,
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
        title: '회원가입'
      }
    ]
  })
})
