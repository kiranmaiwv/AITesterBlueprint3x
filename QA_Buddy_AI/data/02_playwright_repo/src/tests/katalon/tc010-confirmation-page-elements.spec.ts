// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-010: Verify all confirmation page elements after successful booking', async ({
        page,
        curaConfirmationPage,
    }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Complete the full appointment booking flow
        await test.step('Complete appointment booking flow', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
            await page.locator('#combo_facility').selectOption('Tokyo CURA Healthcare Center');
            await page.locator('#radio_program_medicare').check();
            await page.locator('#txt_visit_date').fill('25/03/2026');
            await page.locator('#btn-book-appointment').click();
            await curaConfirmationPage.expectOnConfirmationPage();
        });

        // 2. Verify the page heading
        await test.step('Verify confirmation heading', async () => {
            await expect(page.locator('h2:has-text("Appointment Confirmation")')).toBeVisible();
        });

        // 3. Verify the confirmation message text
        await test.step('Verify confirmation message', async () => {
            await curaConfirmationPage.expectConfirmationMessage();
        });

        // 4. Verify the Facility label and value
        await test.step('Verify Facility label and value', async () => {
            await curaConfirmationPage.expectFacilityLabelVisible();
            await curaConfirmationPage.expectFacility('Tokyo CURA Healthcare Center');
        });

        // 5. Verify the Apply for hospital readmission label and value
        await test.step('Verify readmission label and value', async () => {
            await curaConfirmationPage.expectReadmissionLabelVisible();
            await curaConfirmationPage.expectReadmission('No');
        });

        // 6. Verify the Healthcare Program label and value
        await test.step('Verify Healthcare Program label and value', async () => {
            await curaConfirmationPage.expectProgramLabelVisible();
            await curaConfirmationPage.expectProgram('Medicare');
        });

        // 7. Verify the Visit Date label and value
        await test.step('Verify Visit Date label and value', async () => {
            await curaConfirmationPage.expectVisitDateLabelVisible();
            await curaConfirmationPage.expectVisitDate('25/03/2026');
        });

        // 8. Check if a 'Go to Homepage' link/button is available
        await test.step('Verify Go to Homepage link', async () => {
            await curaConfirmationPage.expectGoToHomepageLinkVisible();
        });
    });
});
