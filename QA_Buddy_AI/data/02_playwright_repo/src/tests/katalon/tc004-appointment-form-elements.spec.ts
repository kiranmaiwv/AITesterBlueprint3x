// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-004: Verify appointment form elements and defaults', async ({ page, curaAppointmentPage }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to appointment form via login
        await test.step('Navigate to appointment form', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
        });

        // 2. Inspect the Facility dropdown
        await test.step('Verify Facility dropdown options', async () => {
            await curaAppointmentPage.expectFacilityDropdownVisible();
            const options = await curaAppointmentPage.getFacilityOptions();
            expect(options).toContain('Tokyo CURA Healthcare Center');
            expect(options).toContain('Hongkong CURA Healthcare Center');
            expect(options).toContain('Seoul CURA Healthcare Center');
        });

        // 3. Inspect the 'Apply for hospital readmission' checkbox
        await test.step('Verify readmission checkbox default state', async () => {
            await curaAppointmentPage.expectReadmissionCheckboxVisible();
            await curaAppointmentPage.expectReadmissionUnchecked();
        });

        // 4. Inspect the Healthcare Program radio buttons
        await test.step('Verify Healthcare Program radio buttons', async () => {
            await expect(page.locator('#radio_program_medicare')).toBeVisible();
            await expect(page.locator('#radio_program_medicaid')).toBeVisible();
            await expect(page.locator('#radio_program_none')).toBeVisible();
        });

        // 5. Inspect the Visit Date field
        await test.step('Verify Visit Date field', async () => {
            await curaAppointmentPage.expectVisitDateFieldVisible();
        });

        // 6. Inspect the Comment textarea
        await test.step('Verify Comment textarea', async () => {
            await curaAppointmentPage.expectCommentFieldVisible();
            await curaAppointmentPage.expectCommentFieldEmpty();
        });

        // 7. Inspect the 'Book Appointment' button
        await test.step('Verify Book Appointment button', async () => {
            await curaAppointmentPage.expectBookAppointmentButtonVisible();
        });
    });
});
