import { expect, Page } from '@playwright/test';

export class CuraConfirmationPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    confirmationHeader = () => this.page.locator('h2:has-text("Appointment Confirmation")');
    confirmationMessage = () => this.page.locator('.lead');
    facilityValue = () => this.page.locator('#facility');
    readmissionValue = () => this.page.locator('#hospital_readmission');
    programValue = () => this.page.locator('#program');
    visitDateValue = () => this.page.locator('#visit_date');
    commentValue = () => this.page.locator('#comment');
    goToHomepageLink = () => this.page.locator('a[href="https://katalon-demo-cura.herokuapp.com/"]');

    facilityLabel = () => this.page.locator('label:has-text("Facility")');
    readmissionLabel = () => this.page.locator('label:has-text("Apply for hospital readmission")');
    programLabel = () => this.page.locator('label:has-text("Healthcare Program")');
    visitDateLabel = () => this.page.locator('label:has-text("Visit Date")');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    async getFacility(): Promise<string> {
        return (await this.facilityValue().textContent()) || '';
    }

    async getReadmission(): Promise<string> {
        return (await this.readmissionValue().textContent()) || '';
    }

    async getProgram(): Promise<string> {
        return (await this.programValue().textContent()) || '';
    }

    async getVisitDate(): Promise<string> {
        return (await this.visitDateValue().textContent()) || '';
    }

    async clickGoToHomepage(): Promise<void> {
        await this.goToHomepageLink().click();
    }

    // ============================================
    // EXPECTATIONS (assertion helpers)
    // ============================================

    async expectOnConfirmationPage(): Promise<void> {
        await expect(this.confirmationHeader()).toBeVisible();
    }

    async expectConfirmationMessage(): Promise<void> {
        await expect(this.confirmationMessage()).toContainText(
            'Please be informed that your appointment has been booked as following:'
        );
    }

    async expectFacility(expected: string): Promise<void> {
        await expect(this.facilityValue()).toHaveText(expected);
    }

    async expectReadmission(expected: string): Promise<void> {
        await expect(this.readmissionValue()).toHaveText(expected);
    }

    async expectProgram(expected: string): Promise<void> {
        await expect(this.programValue()).toHaveText(expected);
    }

    async expectVisitDate(expected: string): Promise<void> {
        await expect(this.visitDateValue()).toHaveText(expected);
    }

    async expectFacilityLabelVisible(): Promise<void> {
        await expect(this.facilityLabel()).toBeVisible();
    }

    async expectReadmissionLabelVisible(): Promise<void> {
        await expect(this.readmissionLabel()).toBeVisible();
    }

    async expectProgramLabelVisible(): Promise<void> {
        await expect(this.programLabel()).toBeVisible();
    }

    async expectVisitDateLabelVisible(): Promise<void> {
        await expect(this.visitDateLabel()).toBeVisible();
    }

    async expectGoToHomepageLinkVisible(): Promise<void> {
        await expect(this.goToHomepageLink()).toBeVisible();
    }
}
