import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@kds/ui/components/button'
import { Input } from '@kds/ui/components/input'
import { useMutation } from '@tanstack/react-query'
import {
  createFileRoute,
  Link as RouterLink,
  redirect
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
import { isLoggedIn, showAuthError } from '@/hooks/use-auth'

const formSchema = z.object({
  email: z.email({ message: '이메일 주소 형식을 확인해 주세요.' })
})

type FormData = z.infer<typeof formSchema>

const RecoverPassword = () => {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: ''
    }
  })

  const recoverPassword = async (data: FormData) => {
    await LoginService.recoverPassword({
      path: { email: data.email }
    })
  }

  const mutation = useMutation({
    mutationFn: recoverPassword,
    onSuccess: () => {
      toast.success('이메일을 확인해 주세요.', {
        description: '가입된 이메일 주소라면 비밀번호 재설정 링크를 보냈어요.'
      })
      form.reset()
    },
    onError: showAuthError
  })

  const onSubmit = async (data: FormData) => {
    if (mutation.isPending) return
    mutation.mutate(data)
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
              비밀번호가 기억나지 않나요?
            </h1>
            <p className="break-keep text-sm text-muted-foreground sm:text-base">
              괜찮아요. 가입한 이메일을 알려주시면 새 비밀번호를 만들 수 있는
              링크를 보내드릴게요.
            </p>
          </div>
          <div className="grid gap-6">
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
              이메일로 링크 받기
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
export const Route = createFileRoute('/recover-password')({
  component: RecoverPassword,
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
        title: '비밀번호 찾기'
      }
    ]
  })
})
