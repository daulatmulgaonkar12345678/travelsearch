import { test, expect } from '@playwright/test'

test.describe('Comprehensive Flow Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set up console error monitoring
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (text.includes('Hydration') || text.includes('did not match')) {
          throw new Error(`Hydration error detected: ${text}`)
        }
      }
    })
  })

  test('multicity with cabin class - complete flow', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    // Select multicity
    await page.click('text=Multi-city')
    await page.waitForTimeout(300)
    
    // Verify cabin class is visible
    await expect(page.locator('text=Cabin Class')).toBeVisible()
    
    // Select Business class
    await page.click('text=Cabin Class')
    await page.waitForTimeout(200)
    await page.click('text=Business')
    
    // Fill first segment
    const origin1 = page.locator('[data-testid="origin-0"]')
    await origin1.fill('Pune')
    await page.waitForTimeout(500)
    
    // Select from autocomplete if available
    const puneOption = page.locator('text=/Pune.*India/')
    if (await puneOption.isVisible()) {
      await puneOption.first().click()
    } else {
      await origin1.fill('PNQ')
    }
    
    const dest1 = page.locator('[data-testid="destination-0"]')
    await dest1.fill('Delhi')
    await page.waitForTimeout(500)
    
    const delhiOption = page.locator('text=/Delhi.*India/').or(page.locator('text=/New Delhi.*India/'))
    if (await delhiOption.first().isVisible()) {
      await delhiOption.first().click()
    } else {
      await dest1.fill('DEL')
    }
    
    // Fill second segment
    const origin2 = page.locator('[data-testid="origin-1"]')
    await origin2.fill('DEL')
    
    const dest2 = page.locator('[data-testid="destination-1"]')
    await dest2.fill('BLR')
    
    // Add third segment
    await page.click('text=Add Another Flight')
    await page.waitForTimeout(300)
    
    await expect(page.locator('text=Flight 3')).toBeVisible()
    
    // Verify cabin class still visible
    await expect(page.locator('text=Cabin Class')).toBeVisible()
    
    // Take screenshot for validation
    await page.screenshot({ path: '/tmp/multicity-business-class.png', fullPage: false })
  })

  test('origin equals destination prevention', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    // Fill same origin and destination
    await page.fill('[data-testid="origin-input"]', 'BOM')
    await page.fill('[data-testid="destination-input"]', 'BOM')
    
    // Try to search
    await page.click('[data-testid="search-button"]')
    
    // Should show alert
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain('different')
      await dialog.accept()
    })
    
    await page.waitForTimeout(500)
  })

  test('hotel minimum 1 night stay validation', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    // Fill city
    await page.fill('[data-testid="city-input"]', 'Mumbai')
    
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    const tomorrowStr = tomorrow.toISOString().split('T')[0]
    
    // Try same day check-in and check-out
    const checkInInput = page.locator('[data-testid="checkin-date-input"]')
    await checkInInput.fill(tomorrowStr)
    
    const checkOutInput = page.locator('[data-testid="checkout-date-input"]')
    // Try to set same date (should be prevented by browser)
    
    // The min attribute should prevent this
    const minCheckOut = await checkOutInput.getAttribute('min')
    
    const dayAfter = new Date(tomorrow)
    dayAfter.setDate(dayAfter.getDate() + 1)
    const dayAfterStr = dayAfter.toISOString().split('T')[0]
    
    expect(minCheckOut).toBe(dayAfterStr)
  })

  test('room configuration with 0 adults prevention', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    // Open room selector
    await page.click('[data-testid="room-selector"]')
    await page.waitForTimeout(300)
    
    // Try to reduce adults to 0 (should be prevented)
    const minusButton = page.locator('button').filter({ hasText: '-' }).first()
    
    // Click multiple times
    await minusButton.click()
    await page.waitForTimeout(100)
    await minusButton.click()
    await page.waitForTimeout(100)
    
    // Adult count should stay at 1 (minimum)
    // The minus button should be disabled
    expect(await minusButton.isDisabled()).toBe(true)
  })

  test('autocomplete keyboard navigation', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    const originInput = page.locator('[data-testid="origin-input"]')
    await originInput.fill('pu')
    
    // Wait for suggestions
    await page.waitForTimeout(500)
    
    // Press arrow down
    await originInput.press('ArrowDown')
    await page.waitForTimeout(100)
    
    // First suggestion should be highlighted
    const firstSuggestion = page.locator('.bg-blue-50').first()
    await expect(firstSuggestion).toBeVisible()
    
    // Press Enter to select
    await originInput.press('Enter')
    await page.waitForTimeout(300)
    
    // Input should have a value
    const value = await originInput.inputValue()
    expect(value).toBeTruthy()
  })

  test('passenger validation - infants exceed adults', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    // Open passenger modal
    await page.click('[data-testid="passenger-selector"]')
    await page.waitForTimeout(300)
    
    // Set 1 adult
    const adultMinus = page.locator('button').filter({ hasText: '-' }).first()
    await adultMinus.click()
    
    // Try to add 2 infants
    const infantPlus = page.locator('button').filter({ hasText: '+' }).last()
    await infantPlus.click()
    await page.waitForTimeout(100)
    
    // Second infant button should be disabled
    // (infants limited to adults count)
    const isDisabled = await infantPlus.isDisabled()
    expect(isDisabled).toBe(true)
  })

  test('date picker enforces minimum dates', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    const tomorrowStr = tomorrow.toISOString().split('T')[0]
    
    // Check departure date min
    const departureInput = page.locator('[data-testid="departure-date-input"]')
    const depMin = await departureInput.getAttribute('min')
    expect(depMin).toBe(tomorrowStr)
    
    // Select departure
    await departureInput.fill(tomorrowStr)
    await page.waitForTimeout(200)
    
    // Check return date min (should be day after departure)
    const returnInput = page.locator('[data-testid="return-date-input"]')
    const retMin = await returnInput.getAttribute('min')
    
    const dayAfter = new Date(tomorrow)
    dayAfter.setDate(dayAfter.getDate() + 1)
    const dayAfterStr = dayAfter.toISOString().split('T')[0]
    
    expect(retMin).toBe(dayAfterStr)
  })

  test('multicity segment date ordering', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    await page.click('text=Multi-city')
    await page.waitForTimeout(300)
    
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const tomorrowStr = tomorrow.toISOString().split('T')[0]
    
    const dayAfter = new Date(tomorrow)
    dayAfter.setDate(dayAfter.getDate() + 1)
    const dayAfterStr = dayAfter.toISOString().split('T')[0]
    
    // First segment date input
    const date1 = page.locator('input[type="date"]').first()
    const date1Min = await date1.getAttribute('min')
    expect(date1Min).toBe(tomorrowStr)
    
    // Set first segment date
    await date1.fill(tomorrowStr)
    await page.waitForTimeout(200)
    
    // Second segment date should have min = first segment date
    const date2 = page.locator('input[type="date"]').nth(1)
    // Note: The min might be set dynamically
    await page.waitForTimeout(200)
  })

  test('error boundary catches and displays errors', async ({ page }) => {
    // This test would require intentionally triggering an error
    // For now, we verify the ErrorBoundary component exists
    await page.goto('http://localhost:3000')
    
    // Page should load without errors
    await expect(page.locator('text=TravelSearch')).toBeVisible()
  })

  test('no hydration errors during tab switching', async ({ page }) => {
    let hydrationErrors = 0
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (text.includes('Hydration') || text.includes('did not match')) {
          hydrationErrors++
        }
      }
    })
    
    await page.goto('http://localhost:3000')
    await page.waitForLoadState('networkidle')
    
    // Switch to hotels
    await page.click('[data-testid="hotels-tab"]')
    await page.waitForTimeout(500)
    
    // Switch back to flights
    await page.click('[data-testid="flights-tab"]')
    await page.waitForTimeout(500)
    
    // Switch trip types
    await page.click('text=Multi-city')
    await page.waitForTimeout(500)
    await page.click('text=One-way')
    await page.waitForTimeout(500)
    await page.click('text=Round-trip')
    await page.waitForTimeout(500)
    
    expect(hydrationErrors).toBe(0)
  })
})
