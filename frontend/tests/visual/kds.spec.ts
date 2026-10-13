import { expect, type Locator, type Page, test } from '@playwright/test'

const openSpecimen = async (
  page: Page,
  storyId: string,
  specimenName: string,
  theme: 'light' | 'dark'
) => {
  const query = new URLSearchParams({
    id: storyId,
    viewMode: 'story',
    globals: `theme:${theme}`
  })
  await page.goto(`iframe.html?${query}`)
  const specimen = page.locator(`[data-component-example="${specimenName}"]`)
  await expect(specimen).toBeVisible()
  await expect(page.locator('html')).toHaveClass(new RegExp(`\\b${theme}\\b`))
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        caret-color: transparent !important;
      }
    `
  })
  return specimen
}

const expectSpecimenScreenshot = async (specimen: Locator, name: string) => {
  await specimen.evaluate(async element => {
    await document.fonts.ready
    await Promise.all(
      Array.from(element.querySelectorAll('img')).map(image => image.decode())
    )
  })
  await expect(specimen).toHaveScreenshot(name)
}

test('action variants', async ({ page, colorScheme }) => {
  const specimen = await openSpecimen(
    page,
    'kds-components-actions--button',
    'button',
    colorScheme === 'dark' ? 'dark' : 'light'
  )
  await expectSpecimenScreenshot(specimen, 'button.png')
})

test('form validation error', async ({ page, colorScheme }) => {
  const specimen = await openSpecimen(
    page,
    'kds-components-forms--input-validation',
    'input-validation',
    colorScheme === 'dark' ? 'dark' : 'light'
  )
  // Storybook's play function finishes in the saved state before this test
  // deliberately returns the form to its invalid state.
  await expect(specimen.getByText('Profile saved for Ada.')).toBeVisible()
  await specimen.getByRole('textbox', { name: 'Display name' }).fill('')
  await specimen.getByRole('button', { name: 'Save profile' }).click()
  await expect(specimen.getByText('Enter a display name.')).toBeVisible()
  await expectSpecimenScreenshot(specimen, 'input-validation.png')
})

test('card surface', async ({ page, colorScheme }) => {
  const specimen = await openSpecimen(
    page,
    'kds-components-surfaces--card',
    'card',
    colorScheme === 'dark' ? 'dark' : 'light'
  )
  await expectSpecimenScreenshot(specimen, 'card.png')
})
