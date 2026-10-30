import { expect, test } from '@playwright/test'

test('login reaches the protected workspace and navigation works', async ({ page }) => {
  const errors: string[] = []
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/login')
  await page.getByLabel('Work email').fill(process.env.DEMO_EMAIL ?? '')
  await page.getByLabel('Password').fill(process.env.DEMO_PASSWORD ?? '')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/app$/)
  await expect(page.getByRole('heading', { name: 'Good morning.' })).toBeVisible()
  await page.getByRole('link', { name: 'Meetings' }).click()
  await expect(page).toHaveURL(/\/app\/meetings$/)
  await expect(page.getByText('Meetings', { exact: true }).first()).toBeVisible()
  expect(errors).toEqual([])
})

test('workspace assistant and meeting capture controls render', async ({ page }) => {
  await page.goto('/app/ask')
  await expect(page.getByText('Ask your workspace.')).toBeVisible()
  await page.goto('/app/meetings/new')
  await page.getByRole('button', { name: 'Upload file' }).click()
  await expect(page.getByText(/TXT, MD, VTT, SRT, DOCX, or PDF/)).toBeVisible()
  await page.getByRole('button', { name: 'Live meeting' }).click()
  await expect(page.getByText(/Live capture is ready/)).toBeVisible()
})

test('all primary application pages respond successfully', async ({ page }) => {
  for (const path of ['/app', '/app/tasks', '/app/knowledge', '/app/context-passports', '/app/activity', '/app/settings', '/app/settings/team']) {
    const response = await page.goto(path)
    expect(response?.status(), path).toBeLessThan(400)
    await expect(page.locator('body')).toBeVisible()
  }
})
