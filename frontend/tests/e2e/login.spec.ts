import { expect, type Page, test } from '@playwright/test'
import { firstSuperuser, firstSuperuserPassword } from './config.ts'
import { randomPassword } from './utils/random.ts'

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, email: string, password: string) => {
  await page.getByTestId('email-input').fill(email)
  await page.getByTestId('password-input').fill(password)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText('')
  await expect(input).toBeEditable()
}

test('Inputs are visible, empty and editable', async ({ page }) => {
  await page.goto('/login')

  await verifyInput(page, 'email-input')
  await verifyInput(page, 'password-input')
})

test('Log in with valid email and password ', async ({ page }) => {
  await page.goto('/login')

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole('button', { name: '로그인' }).click()

  await page.waitForURL('/')
})

test('Log in with invalid email', async ({ page }) => {
  await page.goto('/login')

  await fillForm(page, 'invalidemail', firstSuperuserPassword)
  await page.getByRole('button', { name: '로그인' }).click()

  await expect(page.getByTestId('email-input')).toHaveAttribute(
    'aria-invalid',
    'true'
  )
})

test('Log in with invalid password', async ({ page }) => {
  const password = randomPassword()

  await page.goto('/login')
  await fillForm(page, firstSuperuser, password)
  await page.getByRole('button', { name: '로그인' }).click()

  await expect(
    page.getByText('이메일 또는 비밀번호가 올바르지 않습니다.')
  ).toBeVisible()
})

test('Successful log out', async ({ page }) => {
  await page.goto('/login')

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole('button', { name: '로그인' }).click()

  await page.waitForURL('/')
  await page.getByTestId('user-menu').click()
  await page.getByRole('menuitem', { name: 'Log out' }).click()
  await page.waitForURL('/login')
})

test('Logged-out user cannot access protected routes', async ({ page }) => {
  await page.goto('/login')

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole('button', { name: '로그인' }).click()

  await page.waitForURL('/')
  await page.getByTestId('user-menu').click()
  await page.getByRole('menuitem', { name: 'Log out' }).click()
  await page.waitForURL('/login')

  await page.goto('/settings')
  await page.waitForURL('/login')
})

test('Redirects to /login when token is wrong', async ({ page }) => {
  await page.goto('/settings')
  await page.evaluate(() => {
    localStorage.setItem('access_token', 'invalid_token')
  })
  await page.goto('/settings')
  await page.waitForURL('/login')
  await expect(page).toHaveURL('/login')
})
