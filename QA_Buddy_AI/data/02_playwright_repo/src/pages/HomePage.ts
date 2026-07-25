import { expect, Page } from '@playwright/test';

export class HomePage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    userAvatar = () => this.page.locator('[data-testid="user-avatar"]');
    usernameDisplay = () => this.page.locator('[data-testid="username-display"]');
    logoutButton = () => this.page.locator('[data-testid="logout-button"]');
    navigationMenu = () => this.page.locator('nav');
    searchInput = () => this.page.locator('[data-testid="search-input"]');
    searchButton = () => this.page.locator('[data-testid="search-button"]');
    cartIcon = () => this.page.locator('[data-testid="cart-icon"]');
    cartCount = () => this.page.locator('[data-testid="cart-count"]');
    welcomeMessage = () => this.page.locator('[data-testid="welcome-message"]');
    featuredProducts = () => this.page.locator('[data-testid="featured-products"]');
    categoryMenu = () => this.page.locator('[data-testid="category-menu"]');
    notificationBell = () => this.page.locator('[data-testid="notification-bell"]');
    settingsLink = () => this.page.locator('[data-testid="settings-link"]');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    /**
     * Navigate to the home page
     */
    async navigate(): Promise<void> {
        await this.page.goto('/');
    }

    /**
     * Click the user avatar
     */
    async clickUserAvatar(): Promise<void> {
        await this.userAvatar().click();
    }

    /**
     * Click the logout button
     */
    async clickLogout(): Promise<void> {
        await this.logoutButton().click();
    }

    /**
     * Enter search text
     */
    async enterSearchText(text: string): Promise<void> {
        await this.searchInput().fill(text);
    }

    /**
     * Click the search button
     */
    async clickSearch(): Promise<void> {
        await this.searchButton().click();
    }

    /**
     * Click the cart icon
     */
    async clickCart(): Promise<void> {
        await this.cartIcon().click();
    }

    /**
     * Get the cart count value
     */
    async getCartCount(): Promise<number> {
        const text = await this.cartCount().textContent();
        return parseInt(text || '0', 10);
    }

    /**
     * Get the welcome message text
     */
    async getWelcomeMessage(): Promise<string> {
        return (await this.welcomeMessage().textContent()) || '';
    }

    /**
     * Get the displayed username
     */
    async getDisplayedUsername(): Promise<string> {
        return (await this.usernameDisplay().textContent()) || '';
    }

    /**
     * Click the notification bell
     */
    async clickNotifications(): Promise<void> {
        await this.notificationBell().click();
    }

    /**
     * Click the settings link
     */
    async clickSettings(): Promise<void> {
        await this.settingsLink().click();
    }

    /**
     * Select a category from the menu
     */
    async selectCategory(categoryName: string): Promise<void> {
        await this.categoryMenu().locator(`text="${categoryName}"`).click();
    }

    // ============================================
    // ASSERTIONS (inline expectations)
    // ============================================

    /**
     * Expect user avatar to be visible
     */
    async expectUserAvatarVisible(): Promise<void> {
        await expect(this.userAvatar()).toBeVisible();
    }

    /**
     * Expect to be on the home page
     */
    async expectOnHomePage(): Promise<void> {
        await expect(this.page).toHaveURL(/.*\/(home)?$/);
    }

    /**
     * Expect logout button to be visible
     */
    async expectLogoutButtonVisible(): Promise<void> {
        await expect(this.logoutButton()).toBeVisible();
    }

    /**
     * Expect cart icon to be visible
     */
    async expectCartIconVisible(): Promise<void> {
        await expect(this.cartIcon()).toBeVisible();
    }

    /**
     * Expect welcome message to contain text
     */
    async expectWelcomeMessageContains(text: string): Promise<void> {
        await expect(this.welcomeMessage()).toContainText(text);
    }

    /**
     * Expect featured products section to be visible
     */
    async expectFeaturedProductsVisible(): Promise<void> {
        await expect(this.featuredProducts()).toBeVisible();
    }

    /**
     * Expect search input to be visible
     */
    async expectSearchInputVisible(): Promise<void> {
        await expect(this.searchInput()).toBeVisible();
    }
}

