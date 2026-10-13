import { expect, test } from '@playwright/test'
import { waitForEmailHtml } from './utils/mailpit'
import { randomEmail, randomPassword } from './utils/random'
import { logInUser, signUpNewUser } from './utils/user'

test.use({ storageState: { cookies: [], origins: [] } })

const resetPath = '/reset-password?token='

test('Input is visible, empty and editable', async ({ page }) => {
  await page.goto('/recover-password')

  await expect(page.getByTestId('email-input')).toBeVisible()
  await expect(page.getByTestId('email-input')).toHaveText('')
  await expect(page.getByTestId('email-input')).toBeEditable()
})

test('User can reset password successfully using the link', async ({
  page,
  request
}) => {
  const fullName = 'Test User'
  const email = randomEmail()
  const password = randomPassword()
  const newPassword = randomPassword()

  // Sign up a new user
  await signUpNewUser(page, fullName, email, password)

  await page.goto('/recover-password')
  await page.getByTestId('email-input').fill(email)

  await page.getByRole('button', { name: '이메일로 링크 받기' }).click()

  const emailHtml = await waitForEmailHtml({
    request,
    query: `to:${email}`
  })

  expect(emailHtml).toContain(resetPath)
  const resetUrl = emailHtml.match(/\/reset-password\?token=[^"]+/)?.[0]
  expect(resetUrl).toBeDefined()

  // Set the new password and confirm it
  await page.goto(resetUrl!)

  await page.getByTestId('new-password-input').fill(newPassword)
  await page.getByTestId('confirm-password-input').fill(newPassword)
  await page.getByRole('button', { name: '비밀번호 재설정' }).click()
  await expect(page).toHaveURL(/\/login$/)

  // Check if the user is able to login with the new password
  await logInUser(page, email, newPassword)
})

test('Expired or invalid reset link', async ({ page }) => {
  const password = randomPassword()
  const invalidUrl = '/reset-password?token=invalidtoken'

  await page.goto(invalidUrl)

  await page.getByTestId('new-password-input').fill(password)
  await page.getByTestId('confirm-password-input').fill(password)
  await page.getByRole('button', { name: '비밀번호 재설정' }).click()

  await expect(
    page.getByText(
      '비밀번호 재설정 링크가 유효하지 않거나 만료됐어요. 비밀번호 찾기에서 새 링크를 요청해 주세요.'
    )
  ).toBeVisible()
})

test('Weak new password validation', async ({ page, request }) => {
  const fullName = 'Test User'
  const email = randomEmail()
  const password = randomPassword()
  const weakPassword = '123'

  // Sign up a new user
  await signUpNewUser(page, fullName, email, password)

  await page.goto('/recover-password')
  await page.getByTestId('email-input').fill(email)
  await page.getByRole('button', { name: '이메일로 링크 받기' }).click()

  const emailHtml = await waitForEmailHtml({
    request,
    query: `to:${email}`
  })

  expect(emailHtml).toContain(resetPath)
  const resetUrl = emailHtml.match(/\/reset-password\?token=[^"]+/)?.[0]
  expect(resetUrl).toBeDefined()

  // Set a weak new password
  await page.goto(resetUrl!)
  await page.getByTestId('new-password-input').fill(weakPassword)
  await page.getByTestId('confirm-password-input').fill(weakPassword)
  await page.getByRole('button', { name: '비밀번호 재설정' }).click()

  await expect(page.getByTestId('new-password-input')).toHaveAttribute(
    'aria-invalid',
    'true'
  )
})
