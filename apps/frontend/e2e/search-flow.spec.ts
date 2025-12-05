import { test, expect } from '@playwright/test'

test.describe('Flight Search Flow', () => {
  test('complete search to redirect flow', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/')

    // Fill search form
    await page.getByTestId('origin-input').fill('BOM')
    await page.getByTestId('destination-input').fill('PNQ')
    await page.getByTestId('departure-date-input').fill('2025-12-15')

    // Open passenger modal
    await page.getByTestId('passenger-selector').click()
    await expect(page.getByTestId('passenger-modal')).toBeVisible()

    // Set 2 adults
    await page.getByTestId('increase-adults').click()
    await expect(page.getByTestId('adults-count')).toHaveText('2')

    // Close modal
    await page.getByTestId('done-button').click()
    await expect(page.getByTestId('passenger-modal')).not.toBeVisible()

    // Verify passenger count updated in search bar
    await expect(page.getByTestId('passenger-selector')).toContainText('2 passengers')

    // Submit search
    await page.getByTestId('search-button').click()

    // Wait for results page
    await page.waitForURL(/\/flights\/results/)

    // Wait for results to load
    await expect(page.locator('[data-testid^="result-card-"]').first()).toBeVisible({ timeout: 10000 })

    // Verify results are displayed
    const resultCards = page.locator('[data-testid^="result-card-"]')
    await expect(resultCards).toHaveCount(await resultCards.count())
    expect(await resultCards.count()).toBeGreaterThan(0)

    // Click first provider select button
    const firstProviderSelect = page.locator('[data-testid^="select-provider-"]').first()
    await firstProviderSelect.click()

    // Verify interstitial modal appears
    await expect(page.getByTestId('interstitial-modal')).toBeVisible()

    // Verify countdown is displayed
    await expect(page.locator('[aria-live="polite"]')).toBeVisible()

    // Wait a bit for countdown
    await page.waitForTimeout(1000)

    // Verify redirect information is shown
    await expect(page.getByText(/Redirecting to/)).toBeVisible()
  })

  test('filter functionality', async ({ page }) => {
    // Navigate to search results
    await page.goto('/flights/results?origin=BOM&destination=PNQ&departure_date=2025-12-15&adults=1')

    // Wait for results
    await expect(page.locator('[data-testid^="result-card-"]').first()).toBeVisible({ timeout: 10000 })

    const initialCount = await page.locator('[data-testid^="result-card-"]').count()

    // Open filter sidebar (if mobile)
    const toggleFilters = page.getByTestId('toggle-filters')
    if (await toggleFilters.isVisible()) {
      await toggleFilters.click()
    }

    // Apply non-stop filter
    await page.getByTestId('filter-stop-Non-stop').click()

    // Wait for results to update
    await page.waitForTimeout(500)

    // Verify filtered results
    const filteredCards = page.locator('[data-testid^="result-card-"]')
    const filteredCount = await filteredCards.count()

    // Filtered count should be less than or equal to initial
    expect(filteredCount).toBeLessThanOrEqual(initialCount)
  })

  test('date strip interaction', async ({ page }) => {
    await page.goto('/flights/results?origin=BOM&destination=PNQ&departure_date=2025-12-15&adults=1')

    // Wait for page load
    await page.waitForLoadState('networkidle')

    // Find and click a date in the strip
    const today = new Date()
    today.setDate(today.getDate() + 1) // Tomorrow
    const dateStr = today.toISOString().split('T')[0]

    const dateButton = page.getByTestId(`date-${dateStr}`)
    if (await dateButton.isVisible()) {
      await dateButton.click()

      // Wait for new results
      await page.waitForTimeout(1000)

      // Verify URL updated
      await expect(page).toHaveURL(new RegExp(dateStr))
    }
  })

  test('accessibility - keyboard navigation', async ({ page }) => {
    await page.goto('/')

    // Tab through form elements
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Verify focus is on an input
    const focused = await page.evaluate(() => document.activeElement?.tagName)
    expect(['INPUT', 'BUTTON']).toContain(focused)
  })
})
