import { expect, Page } from '@playwright/test';

export class CuraHomePage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    makeAppointmentButton = () => this.page.locator('#btn-make-appointment');
    brandHeading = () => this.page.locator('h1');
    subHeading = () => this.page.locator('h3');
    toggleNavigationButton = () => this.page.locator('#menu-toggle');
    sidebarMenu = () => this.page.locator('#sidebar-wrapper');
    sidebarHomeLink = () => this.page.locator('a:has-text("Home")');
    sidebarLoginLink = () => this.page.locator('a:has-text("Login")');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    async navigate(): Promise<void> {
        await this.page.goto('https://katalon-demo-cura.herokuapp.com/');
    }

    async clickMakeAppointment(): Promise<void> {
        await this.makeAppointmentButton().click();
    }

    async clickToggleNavigation(): Promise<void> {
        await this.toggleNavigationButton().click();
    }

    async clickSidebarHome(): Promise<void> {
        await this.sidebarHomeLink().click();
    }

    async getBrandHeadingText(): Promise<string> {
        return (await this.brandHeading().textContent()) || '';
    }

    // ============================================
    // EXPECTATIONS (assertion helpers)
    // ============================================

    async expectPageLoaded(): Promise<void> {
        await expect(this.page).toHaveTitle(/CURA Healthcare Service/);
    }

    async expectMakeAppointmentButtonVisible(): Promise<void> {
        await expect(this.makeAppointmentButton()).toBeVisible();
    }

    async expectBrandHeadingVisible(): Promise<void> {
        await expect(this.brandHeading()).toBeVisible();
    }

    async expectToggleNavigationVisible(): Promise<void> {
        await expect(this.toggleNavigationButton()).toBeVisible();
    }

    async expectSidebarMenuVisible(): Promise<void> {
        await expect(this.sidebarMenu()).toBeVisible();
    }

    async expectSidebarMenuItems(): Promise<void> {
        await expect(this.sidebarHomeLink()).toBeVisible();
        await expect(this.sidebarLoginLink()).toBeVisible();
    }
}
