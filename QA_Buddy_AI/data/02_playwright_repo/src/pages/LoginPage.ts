import { expect, Page } from '@playwright/test';

export class LoginPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    usernameInput = () => this.page.locator('#username');
    passwordInput = () => this.page.locator('#password');
    loginButton = () => this.page.locator('button[type="submit"]');
    errorMessage = () => this.page.locator('[data-testid="error-message"]');
    forgotPasswordLink = () => this.page.locator('a:has-text("Forgot Password")');
    rememberMeCheckbox = () => this.page.locator('#remember-me');
    signUpLink = () => this.page.locator('a:has-text("Sign Up")');
    pageTitle = () => this.page.locator('h1');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    /**
     * Navigate to the login page
     */
    async navigate(): Promise<void> {
        await this.page.goto('/login');
    }

    /**
     * Enter username in the username field
     */
    async enterUsername(username: string): Promise<void> {
        await this.usernameInput().fill(username);
    }

    /**
     * Enter password in the password field
     */
    async enterPassword(password: string): Promise<void> {
        await this.passwordInput().fill(password);
    }

    /**
     * Click the login button
     */
    async clickLogin(): Promise<void> {
        await this.loginButton().click();
    }

    /**
     * Click the forgot password link
     */
    async clickForgotPassword(): Promise<void> {
        await this.forgotPasswordLink().click();
    }

    /**
     * Toggle the remember me checkbox
     */
    async toggleRememberMe(): Promise<void> {
        await this.rememberMeCheckbox().click();
    }

    /**
     * Click the sign up link
     */
    async clickSignUp(): Promise<void> {
        await this.signUpLink().click();
    }

    /**
     * Get the error message text
     */
    async getErrorMessage(): Promise<string> {
        return (await this.errorMessage().textContent()) || '';
    }

    /**
     * Get the page title text
     */
    async getPageTitle(): Promise<string> {
        return (await this.pageTitle().textContent()) || '';
    }

    /**
     * Clear the username field
     */
    async clearUsername(): Promise<void> {
        await this.usernameInput().clear();
    }

    /**
     * Clear the password field
     */
    async clearPassword(): Promise<void> {
        await this.passwordInput().clear();
    }

    // ============================================
    // ASSERTIONS (inline expectations)
    // ============================================

    /**
     * Expect error message to be visible
     */
    async expectErrorVisible(): Promise<void> {
        await expect(this.errorMessage()).toBeVisible();
    }

    /**
     * Expect error message to be hidden
     */
    async expectErrorHidden(): Promise<void> {
        await expect(this.errorMessage()).toBeHidden();
    }

    /**
     * Expect login button to be enabled
     */
    async expectLoginButtonEnabled(): Promise<void> {
        await expect(this.loginButton()).toBeEnabled();
    }

    /**
     * Expect login button to be disabled
     */
    async expectLoginButtonDisabled(): Promise<void> {
        await expect(this.loginButton()).toBeDisabled();
    }

    /**
     * Expect to be on the login page
     */
    async expectOnLoginPage(): Promise<void> {
        await expect(this.page).toHaveURL(/.*login.*/);
    }

    /**
     * Expect username field to be visible
     */
    async expectUsernameFieldVisible(): Promise<void> {
        await expect(this.usernameInput()).toBeVisible();
    }

    /**
     * Expect password field to be visible
     */
    async expectPasswordFieldVisible(): Promise<void> {
        await expect(this.passwordInput()).toBeVisible();
    }
}

