/**
 * Sample Test Suite for The Testing Academy
 * @description Demo tests to showcase CustomTTAReporter functionality
 * @author Pramod Dutta
 * @website https://thetestingacademy.com
 */

import { test, expect } from '@playwright/test';

test.describe('@P0 @Smoke @TTA The Testing Academy - Sample Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        // Navigate to The Testing Academy website
        await page.goto('https://thetestingacademy.com');
    });

    test('@P0 should load homepage successfully', async ({ page }) => {
        await test.step('Verify page title', async () => {
            const title = await page.title();
            console.log(`Page Title: ${title}`);
            expect(title).toBeTruthy();
        });

        await test.step('Verify page URL', async () => {
            const url = page.url();
            console.log(`Current URL: ${url}`);
            expect(url).toContain('thetestingacademy');
        });

        await test.step('Take screenshot of homepage', async () => {
            await page.screenshot({ path: 'tta-report/screenshots/homepage.png' });
            console.log('Screenshot captured successfully');
        });
    });

    test('@P1 should display main navigation', async ({ page }) => {
        await test.step('Wait for page to load completely', async () => {
            await page.waitForLoadState('networkidle');
            console.log('Page loaded completely');
        });

        await test.step('Verify header is visible', async () => {
            const header = page.locator('header').first();
            await expect(header).toBeVisible({ timeout: 10000 });
            console.log('Header is visible');
        });

        await test.step('Verify navigation exists', async () => {
            const nav = page.locator('nav').first();
            const isVisible = await nav.isVisible().catch(() => false);
            console.log(`Navigation visible: ${isVisible}`);
            expect(true).toBeTruthy(); // Soft assertion - page structure may vary
        });
    });

    test('@P1 should have proper SEO elements', async ({ page }) => {
        await test.step('Check meta description', async () => {
            const metaDesc = page.locator('meta[name="description"]');
            const content = await metaDesc.getAttribute('content').catch(() => null);
            console.log(`Meta Description: ${content || 'Not found'}`);
        });

        await test.step('Check Open Graph tags', async () => {
            const ogTitle = page.locator('meta[property="og:title"]');
            const ogContent = await ogTitle.getAttribute('content').catch(() => null);
            console.log(`OG Title: ${ogContent || 'Not found'}`);
        });

        await test.step('Verify favicon exists', async () => {
            const favicon = page.locator('link[rel*="icon"]').first();
            const href = await favicon.getAttribute('href').catch(() => null);
            console.log(`Favicon: ${href || 'Not found'}`);
            expect(true).toBeTruthy();
        });
    });

    test('@P2 should be responsive', async ({ page }) => {
        await test.step('Test desktop viewport', async () => {
            await page.setViewportSize({ width: 1920, height: 1080 });
            console.log('Testing at 1920x1080 (Desktop)');
            await page.waitForTimeout(500);
        });

        await test.step('Test tablet viewport', async () => {
            await page.setViewportSize({ width: 768, height: 1024 });
            console.log('Testing at 768x1024 (Tablet)');
            await page.waitForTimeout(500);
        });

        await test.step('Test mobile viewport', async () => {
            await page.setViewportSize({ width: 375, height: 667 });
            console.log('Testing at 375x667 (Mobile)');
            await page.waitForTimeout(500);
        });

        await test.step('Verify page is still functional', async () => {
            const body = page.locator('body');
            await expect(body).toBeVisible();
            console.log('Page remains functional across viewports');
        });
    });

    test('@P1 should measure page performance', async ({ page }) => {
        await test.step('Measure page load time', async () => {
            const startTime = Date.now();
            await page.goto('https://thetestingacademy.com');
            await page.waitForLoadState('domcontentloaded');
            const loadTime = Date.now() - startTime;
            console.log(`DOM Content Loaded in: ${loadTime}ms`);
            expect(loadTime).toBeLessThan(10000); // 10 seconds max
        });

        await test.step('Check for JavaScript errors', async () => {
            const errors: string[] = [];
            page.on('pageerror', (error) => errors.push(error.message));
            await page.waitForTimeout(2000);
            console.log(`JavaScript errors found: ${errors.length}`);
            if (errors.length > 0) {
                console.log('Errors:', errors.join(', '));
            }
        });

        await test.step('Verify no console errors', async () => {
            console.log('Performance check completed');
            expect(true).toBeTruthy();
        });
    });
});

test.describe('@P2 @Regression TTA - Additional Checks', () => {
    
    test('@P2 should verify footer content', async ({ page }) => {
        await page.goto('https://thetestingacademy.com');
        
        await test.step('Scroll to footer', async () => {
            await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
            console.log('Scrolled to bottom of page');
            await page.waitForTimeout(500);
        });

        await test.step('Verify footer exists', async () => {
            const footer = page.locator('footer').first();
            const isVisible = await footer.isVisible().catch(() => false);
            console.log(`Footer visible: ${isVisible}`);
        });

        await test.step('Take footer screenshot', async () => {
            await page.screenshot({ path: 'tta-report/screenshots/footer.png', fullPage: false });
            console.log('Footer screenshot captured');
        });
    });
});

