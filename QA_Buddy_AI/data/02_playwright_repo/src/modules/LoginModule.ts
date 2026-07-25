import { Page } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { HomePage } from '../pages/HomePage';
import { Logger } from '../utils/Logger';

export class LoginModule {
    private page: Page;
    private loginPage: LoginPage;
    private homePage: HomePage;
    private logger: Logger;

    constructor(page: Page) {
        this.page = page;
        this.loginPage = new LoginPage(page);
        this.homePage = new HomePage(page);
        this.logger = Logger.create('LoginModule');
    }

    /**
     * Perform complete login flow with valid credentials
     */
    async doLogin(username: string, password: string): Promise<boolean> {
        this.logger.step(1, 'Navigate to login page');
        await this.loginPage.navigate();

        this.logger.step(2, 'Enter username');
        await this.loginPage.enterUsername(username);

        this.logger.step(3, 'Enter password');
        await this.loginPage.enterPassword(password);

        this.logger.step(4, 'Click login button');
        await this.loginPage.clickLogin();

        this.logger.step(5, 'Wait for redirect to home page');
        await this.page.waitForURL('**/home');

        this.logger.info('Login successful');
        return true;
    }

    /**
     * Attempt login with invalid credentials and return error message
     */
    async attemptInvalidLogin(username: string, password: string): Promise<string> {
        this.logger.step(1, 'Navigate to login page');
        await this.loginPage.navigate();

        this.logger.step(2, 'Enter invalid username');
        await this.loginPage.enterUsername(username);

        this.logger.step(3, 'Enter invalid password');
        await this.loginPage.enterPassword(password);

        this.logger.step(4, 'Click login button');
        await this.loginPage.clickLogin();

        this.logger.step(5, 'Wait for error message');
        await this.loginPage.expectErrorVisible();

        const errorMessage = await this.loginPage.getErrorMessage();
        this.logger.info(`Login failed with message: ${errorMessage}`);
        return errorMessage;
    }

    /**
     * Verify the user is logged in
     */
    async verifyLoggedIn(): Promise<void> {
        this.logger.info('Verifying user is logged in');
        await this.homePage.expectUserAvatarVisible();
        this.logger.info('User is logged in');
    }

    /**
     * Verify the user is logged out
     */
    async verifyLoggedOut(): Promise<void> {
        this.logger.info('Verifying user is logged out');
        await this.loginPage.expectOnLoginPage();
        this.logger.info('User is logged out');
    }

    /**
     * Perform logout flow
     */
    async doLogout(): Promise<void> {
        this.logger.step(1, 'Click user avatar');
        await this.homePage.clickUserAvatar();

        this.logger.step(2, 'Click logout button');
        await this.homePage.clickLogout();

        this.logger.step(3, 'Wait for redirect to login page');
        await this.page.waitForURL('**/login');

        this.logger.info('Logout successful');
    }

    /**
     * Navigate to forgot password page
     */
    async goToForgotPassword(): Promise<void> {
        this.logger.step(1, 'Navigate to login page');
        await this.loginPage.navigate();

        this.logger.step(2, 'Click forgot password link');
        await this.loginPage.clickForgotPassword();

        this.logger.info('Navigated to forgot password page');
    }

    /**
     * Navigate to sign up page
     */
    async goToSignUp(): Promise<void> {
        this.logger.step(1, 'Navigate to login page');
        await this.loginPage.navigate();

        this.logger.step(2, 'Click sign up link');
        await this.loginPage.clickSignUp();

        this.logger.info('Navigated to sign up page');
    }

    /**
     * Login with remember me option enabled
     */
    async doLoginWithRememberMe(username: string, password: string): Promise<boolean> {
        this.logger.step(1, 'Navigate to login page');
        await this.loginPage.navigate();

        this.logger.step(2, 'Enter username');
        await this.loginPage.enterUsername(username);

        this.logger.step(3, 'Enter password');
        await this.loginPage.enterPassword(password);

        this.logger.step(4, 'Enable remember me');
        await this.loginPage.toggleRememberMe();

        this.logger.step(5, 'Click login button');
        await this.loginPage.clickLogin();

        this.logger.step(6, 'Wait for redirect to home page');
        await this.page.waitForURL('**/home');

        this.logger.info('Login with remember me successful');
        return true;
    }
}

