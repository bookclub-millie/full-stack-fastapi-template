import type { Page } from '@playwright/test'

export const signUpNewUser = async (
  page: Page,
  name: string,
  email: string,
  password: string
) => {
  await page.goto('/signup')

  await page.getByTestId('full-name-input').fill(name)
  await page.getByTestId('email-input').fill(email)
  await page.getByTestId('password-input').fill(password)
  await page.getByTestId('confirm-password-input').fill(password)
  await page.getByRole('button', { name: '회원가입' }).click()
  await page.goto('/login')
}

export const logInUser = async (
  page: Page,
  email: string,
  password: string
) => {
  await page.goto('/login')

  await page.getByTestId('email-input').fill(email)
  await page.getByTestId('password-input').fill(password)
  await page.getByRole('button', { name: '로그인' }).click()
  await page.waitForURL('/')
}

export const logOutUser = async (page: Page) => {
  await page.getByTestId('user-menu').click()
  await page.getByRole('menuitem', { name: 'Log out' }).click()
  await page.goto('/login')
}
