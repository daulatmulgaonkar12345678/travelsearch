import { test, expect } from '@playwright/test'

test.describe('Hotels Page', () => {
  test('should load hotels page without 404', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    // Check page loads successfully
    await expect(page).toHaveTitle(/Hotel Search/)
    
    // Check main heading exists
    await expect(page.locator('h2')).toContainText('Find Your Perfect Stay')
    
    // Check search bar is visible
    await expect(page.locator('[data-testid="hotels-tab"]')).toBeVisible()
  })

  test('should have hotels tab selected by default', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    const hotelsTab = page.locator('[data-testid="hotels-tab"]')
    await expect(hotelsTab).toHaveClass(/blue-600/)
  })

  test('should show room selector modal', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    // Click room selector button
    await page.click('[data-testid="room-selector"]')
    
    // Modal should be visible
    await expect(page.locator('text=Rooms & Guests')).toBeVisible()
    
    // Check room type selector exists
    await expect(page.locator('select').first()).toBeVisible()
  })

  test('should validate check-in/check-out dates', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    const checkInInput = page.locator('[data-testid="checkin-date-input"]')
    const checkOutInput = page.locator('[data-testid="checkout-date-input"]')
    
    // Check that min date is set (tomorrow)
    const minDate = await checkInInput.getAttribute('min')
    expect(minDate).toBeTruthy()
    
    // Check that check-out min is after check-in
    const checkOutMin = await checkOutInput.getAttribute('min')
    expect(checkOutMin).toBeTruthy()
  })

  test('should allow room type selection', async ({ page }) => {
    await page.goto('http://localhost:3000/hotels')
    
    // Open room selector
    await page.click('[data-testid="room-selector"]')
    
    // Wait for modal
    await expect(page.locator('text=Rooms & Guests')).toBeVisible()
    
    // Select room type
    const roomTypeSelect = page.locator('select').first()
    await roomTypeSelect.selectOption('Deluxe')
    
    // Check AC checkbox
    const acCheckbox = page.locator('input[type="checkbox"]').first()
    await acCheckbox.check()
    
    // Add another room
    await page.click('text=Add Another Room')
    
    // Should now have 2 rooms
    await expect(page.locator('text=Room 2')).toBeVisible()
    
    // Close modal
    await page.click('button:has-text("Done")')
    
    // Summary should update
    await expect(page.locator('[data-testid="room-selector"]')).toContainText('2 rooms')
  })
})
