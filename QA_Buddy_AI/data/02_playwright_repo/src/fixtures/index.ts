import { test as base, Page } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { HomePage } from '../pages/HomePage';
import { ProductPage } from '../pages/ProductPage';
import { CheckoutPage } from '../pages/CheckoutPage';
import { LoginModule } from '../modules/LoginModule';
import { ProductModule } from '../modules/ProductModule';
import { CheckoutModule } from '../modules/CheckoutModule';
import { config } from '../config';

export type TestFixtures = {
    // Page Objects
    loginPage: LoginPage;
    homePage: HomePage;
    productPage: ProductPage;
    checkoutPage: CheckoutPage;
    
    // Modules
    loginModule: LoginModule;
    productModule: ProductModule;
    checkoutModule: CheckoutModule;
    
    // Pre-authenticated page
    authenticatedPage: Page;
};

export const test = base.extend<TestFixtures>({
    /**
     * Login Page fixture
     */
    loginPage: async ({ page }, use) => {
        await use(new LoginPage(page));
    },

    /**
     * Home Page fixture
     */
    homePage: async ({ page }, use) => {
        await use(new HomePage(page));
    },

    /**
     * Product Page fixture
     */
    productPage: async ({ page }, use) => {
        await use(new ProductPage(page));
    },

    /**
     * Checkout Page fixture
     */
    checkoutPage: async ({ page }, use) => {
        await use(new CheckoutPage(page));
    },

    /**
     * Login Module fixture
     */
    loginModule: async ({ page }, use) => {
        await use(new LoginModule(page));
    },

    /**
     * Product Module fixture
     */
    productModule: async ({ page }, use) => {
        await use(new ProductModule(page));
    },

    /**
     * Checkout Module fixture
     */
    checkoutModule: async ({ page }, use) => {
        await use(new CheckoutModule(page));
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
        await page.waitForURL('**/home');

        await use(page);
        await context.close();
    },
});

export { expect } from '@playwright/test';

// Re-export auth fixtures
export { authTest, authenticatedTest } from './auth.fixture';

