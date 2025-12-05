import { test, expect } from '@playwright/test'

test.describe('Complete Search Flows', () => {
  test('flight roundtrip search with autocomplete', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    // Type in origin
    const originInput = page.locator('[data-testid="origin-input"]')
    await originInput.fill('Pune')
    
    // Wait for suggestions
    await page.waitForTimeout(500)
    
    // Click on Pune suggestion if available
    const puneOption = page.locator('text=/Pune.*India/')
    if (await puneOption.isVisible()) {
      await puneOption.first().click()
    }
    
    // Type in destination
    const destInput = page.locator('[data-testid="destination-input"]')
    await destInput.fill('Mumbai')
    await page.waitForTimeout(500)
    
    // Select Mumbai if available
    const mumbaiOption = page.locator('text=/Mumbai.*India/')
    if (await mumbaiOption.isVisible()) {
      await mumbaiOption.first().click()
    }
    
    // Select cabin class
    await page.click('text=Cabin Class')
    await page.click('text=Business')
    
    // Check no hydration errors in console
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('Hydration')) {
        errors.push(msg.text())
      }
    })
    
    await page.waitForTimeout(1000)
    expect(errors.length).toBe(0)
  })

  test('multicity flight with cabin class', async ({ page }) => {
    await page.goto('http://localhost:3000')
    
    // Click multicity
    await page.click('text=Multi-city')
    
    // Verify cabin class selector is visible
    await expect(page.locator('text=Cabin Class')).toBeVisible()
    
    // Select First class
    await page.click('text=Cabin Class')
    await page.click('text=First Class')
    
    // Fill first segment
    const origin1 = page.locator('[data-testid="origin-0"]')
    await origin1.fill('PNQ')
    
    const dest1 = page.locator('[data-testid="destination-0"]')
    await dest1.fill('DEL')
    
    // Verify dates are set to tomorrow+
    const date1Input = page.locator('input[type="date"]').first()
    const minDate = await date1Input.getAttribute('min')
    expect(minDate).toBeTruthy()
    
    // Add another segment
    await page.click('text=Add Another Flight')
    await expect(page.locator('text=Flight 3')).toBeVisible()
  })

  test('hotel search with room selector', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    // Verify hotels tab is selected
    const hotelsTab = page.locator('[data-testid="hotels-tab"]')
    await expect(hotelsTab).toHaveClass(/blue-600/)
    
    // Fill city
    const cityInput = page.locator('[data-testid="city-input"]')
    await cityInput.fill('Mumbai')
    
    // Open room selector
    await page.click('[data-testid="room-selector"]')
    
    // Wait for modal
    await expect(page.locator('text=Rooms & Guests')).toBeVisible()
    
    // Select room type
    const roomTypeSelect = page.locator('select').first()
    await roomTypeSelect.selectOption('Deluxe')
    
    // Toggle AC
    const acCheckbox = page.locator('input[type="checkbox"]').first()
    await acCheckbox.check()
    
    // Verify AC is checked
    expect(await acCheckbox.isChecked()).toBe(true)
    
    // Add second room
    await page.click('text=Add Another Room')
    await expect(page.locator('text=Room 2')).toBeVisible()
    
    // Done
    await page.click('button:has-text("Done")')
    
    // Verify summary updated
    await expect(page.locator('[data-testid="room-selector"]')).toContainText('2 rooms')
  })

  test('date validation prevents invalid dates', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    const checkInInput = page.locator('[data-testid="checkin-date-input"]')
    const checkOutInput = page.locator('[data-testid="checkout-date-input"]')
    
    // Get tomorrow's date
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const tomorrowStr = tomorrow.toISOString().split('T')[0]
    
    // Check minimum is set
    const minDate = await checkInInput.getAttribute('min')
    expect(minDate).toBe(tomorrowStr)
    
    // Set check-in
    await checkInInput.fill(tomorrowStr)
    
    // Check-out min should be day after check-in
    const dayAfter = new Date(tomorrow)
    dayAfter.setDate(dayAfter.getDate() + 1)
    const dayAfterStr = dayAfter.toISOString().split('T')[0]
    
    const checkOutMin = await checkOutInput.getAttribute('min')
    expect(checkOutMin).toBe(dayAfterStr)
  })

  test('no hydration errors on page load', async ({ page }) => {
    const errors: string[] = []
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (text.includes('Hydration') || text.includes('did not match')) {
          errors.push(text)
        }
      }
    })
    
    await page.goto('http://localhost:3000')
    await page.waitForLoadState('networkidle')
    
    // Navigate to hotels
    await page.goto('http://localhost:3000/hotels')
    await page.waitForLoadState('networkidle')
    
    // Check no hydration errors
    expect(errors).toEqual([])
  })
})
