import { test as base, Page, BrowserContext } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { config } from '../config';

export interface AuthFixture {
    authenticatedPage: Page;
    authenticatedContext: BrowserContext;
}

/**
 * Create a fixture with pre-authenticated page
 */
export const authTest = base.extend<AuthFixture>({
    /**
     * Pre-authenticated browser context
     */
    authenticatedContext: async ({ browser }, use) => {
        const context = await browser.newContext();
        const page = await context.newPage();

        // Perform login
        const loginPage = new LoginPage(page);
        await loginPage.navigate();
        await loginPage.enterUsername(config.testUser.username);
        await loginPage.enterPassword(config.testUser.password);
        await loginPage.clickLogin();
        
        // Wait for successful login
        await page.waitForURL('**/home');

        // Store authentication state
        await context.storageState({ path: '.auth/user.json' });

        await use(context);
        await context.close();
    },

    /**
     * Pre-authenticated page fixture
     */
    authenticatedPage: async ({ browser }, use) => {
        const context = await browser.newContext();
        const page = await context.newPage();

        // Perform login
        const loginPage = new LoginPage(page);
        await loginPage.navigate();
        await loginPage.enterUsername(config.testUser.username);
        await loginPage.enterPassword(config.testUser.password);
        await loginPage.clickLogin();
        
        // Wait for successful login
        await page.waitForURL('**/home');

        await use(page);
        await context.close();
    },
});

/**
 * Create a fixture using stored authentication state
 */
export const authenticatedTest = base.extend<{ page: Page }>({
    page: async ({ browser }, use) => {
        try {
            // Try to use stored auth state
            const context = await browser.newContext({
                storageState: '.auth/user.json',
            });
            const page = await context.newPage();
            await use(page);
            await context.close();
        } catch {
            // Fall back to fresh login if no stored state
            const context = await browser.newContext();
            const page = await context.newPage();

            const loginPage = new LoginPage(page);
            await loginPage.navigate();
            await loginPage.enterUsername(config.testUser.username);
            await loginPage.enterPassword(config.testUser.password);
            await loginPage.clickLogin();
            await page.waitForURL('**/home');

            await use(page);
            await context.close();
        }
    },
});

