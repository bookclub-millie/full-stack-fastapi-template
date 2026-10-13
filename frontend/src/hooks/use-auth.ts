import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'

import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService
} from '@/client'
import { handleError } from '@/utils'

const isLoggedIn = () => {
  return localStorage.getItem('access_token') !== null
}

const authErrorMessages: Record<string, string> = {
  'Incorrect email or password': '이메일 또는 비밀번호를 확인해 주세요.',
  'Inactive user': '비활성화된 계정이에요. 관리자에게 문의해 주세요.',
  'The user with this email already exists in the system':
    '이미 가입된 이메일이에요. 로그인하거나 다른 이메일을 입력해 주세요.',
  'Invalid token':
    '비밀번호 재설정 링크가 유효하지 않거나 만료됐어요. 비밀번호 찾기에서 새 링크를 요청해 주세요.'
}

export const showAuthError = (error: Error) => {
  handleError.call(message => {
    toast.error('요청을 처리하지 못했어요.', {
      description:
        authErrorMessages[message] ??
        '오류가 발생했어요. 잠시 후 다시 시도해 주세요.'
    })
  }, error)
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ['currentUser'],
    queryFn: async () => (await UsersService.readUserMe()).data,
    enabled: isLoggedIn()
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ body: data }),
    onSuccess: () => {
      navigate({ to: '/login' })
    },
    onError: showAuthError,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    }
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      body: data
    })
    localStorage.setItem('access_token', response.data.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: '/' })
    },
    onError: showAuthError
  })

  const logout = () => {
    localStorage.removeItem('access_token')
    navigate({ to: '/login' })
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user
  }
}

export { isLoggedIn }
export default useAuth
