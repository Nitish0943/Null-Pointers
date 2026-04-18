import { test, expect } from '@playwright/test';

test.describe('Agentic Digital Twin Dashboard', () => {
  test('should render main operation panels', async ({ page }) => {
    await page.goto('http://localhost:3000/');
    
    // Check Header
    await expect(page.getByText('Fluidd Twin')).toBeVisible();
    
    // Check State Panel
    await expect(page.getByText('MACHINE STATE')).toBeVisible();
    
    // Check Telemetry Charts
    await expect(page.getByText('POSITIONAL DATA')).toBeVisible();
    await expect(page.getByText('THERMAL DYNAMICS')).toBeVisible();
  });

  test('should navigate to Admin Center', async ({ page }) => {
    await page.goto('http://localhost:3000/admin');
    
    await expect(page.getByText('Administrator Dashboard')).toBeVisible();
    await expect(page.getByText('MAINTENANCE RECOVERY CENTER')).toBeVisible();
    await expect(page.getByText('GLOBAL PRODUCTION IMPACT SUMMARY')).toBeVisible();
  });

  test('should toggle voice link on Agents page', async ({ page }) => {
    await page.goto('http://localhost:3000/agents');
    
    const voiceBtn = page.getByText('Enable Voice Link');
    await expect(voiceBtn).toBeVisible();
    await voiceBtn.click();
    await expect(page.getByText('Voice Link Active')).toBeVisible();
  });
});
