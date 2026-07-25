import { expect, Page } from '@playwright/test';

export class CuraLoginPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    usernameInput = () => this.page.locator('#txt-username');
    passwordInput = () => this.page.locator('#txt-password');
    loginButton = () => this.page.locator('#btn-login');
    loginHeader = () => this.page.locator('h2:has-text("Login")');
    errorMessage = () => this.page.locator('.text-danger');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    async enterUsername(username: string): Promise<void> {
        await this.usernameInput().fill(username);
    }

    async enterPassword(password: string): Promise<void> {
        await this.passwordInput().fill(password);
    }

    async clickLogin(): Promise<void> {
        await this.loginButton().click();
    }

    async getErrorMessage(): Promise<string> {
        return (await this.errorMessage().textContent()) || '';
    }

    // ============================================
    // EXPECTATIONS (assertion helpers)
    // ============================================

    async expectOnLoginPage(): Promise<void> {
        await expect(this.loginHeader()).toBeVisible();
    }

    async expectUsernameFieldVisible(): Promise<void> {
        await expect(this.usernameInput()).toBeVisible();
    }

    async expectPasswordFieldVisible(): Promise<void> {
        await expect(this.passwordInput()).toBeVisible();
    }

    async expectLoginButtonVisible(): Promise<void> {
        await expect(this.loginButton()).toBeVisible();
    }

    async expectPasswordFieldMasked(): Promise<void> {
        await expect(this.passwordInput()).toHaveAttribute('type', 'password');
    }

    async expectErrorVisible(): Promise<void> {
        await expect(this.errorMessage()).toBeVisible();
    }
}
