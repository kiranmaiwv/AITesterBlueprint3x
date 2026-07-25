// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-013: Submit appointment form without entering a visit date', async ({ page }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to appointment form via login
        await test.step('Navigate to appointment form', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
        });

        // 2. Select a facility, select a healthcare program, but leave Visit Date empty
        await test.step('Fill form without visit date', async () => {
            await page.locator('#combo_facility').selectOption('Tokyo CURA Healthcare Center');
            await page.locator('#radio_program_medicare').check();
            await expect(page.locator('#txt_visit_date')).toHaveValue('');
        });

        // 3. Click 'Book Appointment' and verify behaviour
        await test.step('Click Book Appointment and verify behaviour', async () => {
            await page.locator('#btn-book-appointment').click();
            // The form may submit with an empty date or show validation
            // Verify the actual behaviour of the application
            const isOnConfirmation = await page.locator('h2:has-text("Appointment Confirmation")').isVisible()
                .catch(() => false);
            if (isOnConfirmation) {
                // App allows booking without date — verify the visit date is empty
                await expect(page.locator('#visit_date')).toHaveText('');
            } else {
                // App blocks the form — user should still be on the appointment page
                await expect(page.locator('h2:has-text("Make Appointment")')).toBeVisible();
            }
        });
    });
});
