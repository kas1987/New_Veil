import { expect, test } from '@playwright/test'

test('full-stack React client talks to live FastAPI game engine', async ({ page, request }) => {
  const statusRes = await request.get('/api/runtime/status')
  expect(statusRes.ok()).toBeTruthy()

  const resetRes = await request.post('/api/game/reset')
  expect(resetRes.ok()).toBeTruthy()
  const resetBody = await resetRes.json()
  expect(resetBody.ok).toBeTruthy()

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Caetherra Sunlit Plaza' })).toBeVisible()
  await expect(page.getByText(/Surface Walker/i).first()).toBeVisible()
  await expect(page.getByRole('button', { name: /Mira/i })).toBeVisible()

  // Live backend object inspection over HTTP -> SQLite
  await page.getByRole('button', { name: /Inspect: Lantern/i }).click()
  await expect
    .poll(async () => {
      const res = await request.get('/api/game/state')
      const body = await res.json()
      const lantern = (body.objects_here || []).find((o: { id: string }) => o.id === 'lantern')
      return Boolean(lantern?.inspected_prism)
    })
    .toBe(true)

  // Live Veil state advance over HTTP -> SQLite
  await page.getByRole('button', { name: /Veil:/i }).click()
  await expect
    .poll(async () => {
      const res = await request.get('/api/game/state')
      const body = await res.json()
      return body.world.veil_state
    })
    .not.toBe('calm')

  // Open Quest Journal drawer via ghost rail button
  await page.getByRole('button', { name: /Quest Journal/i }).click()
  await expect(page.getByRole('complementary')).toBeVisible()
  await expect(page.getByText('The First Light')).toBeVisible()
})
