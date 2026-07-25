import { expect, Page } from '@playwright/test';

export class CuraAppointmentPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    facilitySelect = () => this.page.locator('#combo_facility');
    readmissionCheckbox = () => this.page.locator('#chk_hosp498');
    medicareRadio = () => this.page.locator('#radio_program_medicare');
    medicaidRadio = () => this.page.locator('#radio_program_medicaid');
    noneRadio = () => this.page.locator('#radio_program_none');
    visitDateInput = () => this.page.locator('#txt_visit_date');
    commentTextarea = () => this.page.locator('#txt_comment');
    bookAppointmentButton = () => this.page.locator('#btn-book-appointment');
    appointmentHeader = () => this.page.locator('h2:has-text("Make Appointment")');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    async selectFacility(facility: string): Promise<void> {
        await this.facilitySelect().selectOption(facility);
    }

    async checkReadmission(): Promise<void> {
        await this.readmissionCheckbox().check();
    }

    async selectMedicare(): Promise<void> {
        await this.medicareRadio().check();
    }

    async selectMedicaid(): Promise<void> {
        await this.medicaidRadio().check();
    }

    async selectNone(): Promise<void> {
        await this.noneRadio().check();
    }

    async enterVisitDate(date: string): Promise<void> {
        await this.visitDateInput().fill(date);
    }

    async enterComment(comment: string): Promise<void> {
        await this.commentTextarea().fill(comment);
    }

    async clickBookAppointment(): Promise<void> {
        await this.bookAppointmentButton().click();
    }

    async getFacilityOptions(): Promise<string[]> {
        return await this.facilitySelect().locator('option').allTextContents();
    }

    // ============================================
    // EXPECTATIONS (assertion helpers)
    // ============================================

    async expectOnAppointmentPage(): Promise<void> {
        await expect(this.appointmentHeader()).toBeVisible();
    }

    async expectFacilityDropdownVisible(): Promise<void> {
        await expect(this.facilitySelect()).toBeVisible();
    }

    async expectReadmissionCheckboxVisible(): Promise<void> {
        await expect(this.readmissionCheckbox()).toBeVisible();
    }

    async expectReadmissionUnchecked(): Promise<void> {
        await expect(this.readmissionCheckbox()).not.toBeChecked();
    }

    async expectReadmissionChecked(): Promise<void> {
        await expect(this.readmissionCheckbox()).toBeChecked();
    }

    async expectMedicareSelected(): Promise<void> {
        await expect(this.medicareRadio()).toBeChecked();
    }

    async expectMedicaidSelected(): Promise<void> {
        await expect(this.medicaidRadio()).toBeChecked();
    }

    async expectNoneSelected(): Promise<void> {
        await expect(this.noneRadio()).toBeChecked();
    }

    async expectVisitDateFieldVisible(): Promise<void> {
        await expect(this.visitDateInput()).toBeVisible();
    }

    async expectCommentFieldVisible(): Promise<void> {
        await expect(this.commentTextarea()).toBeVisible();
    }

    async expectCommentFieldEmpty(): Promise<void> {
        await expect(this.commentTextarea()).toHaveValue('');
    }

    async expectBookAppointmentButtonVisible(): Promise<void> {
        await expect(this.bookAppointmentButton()).toBeVisible();
    }
}
