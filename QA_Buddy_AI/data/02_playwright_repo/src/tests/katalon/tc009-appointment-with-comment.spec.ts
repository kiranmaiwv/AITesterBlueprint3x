// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-009: Book appointment with a comment', async ({ page }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to appointment form via login
        await test.step('Navigate to appointment form', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
        });

        // 2. Select facility, leave readmission unchecked, select Medicare, enter date
        await test.step('Fill appointment form fields', async () => {
            await page.locator('#combo_facility').selectOption('Tokyo CURA Healthcare Center');
            await expect(page.locator('#chk_hosp498')).not.toBeChecked();
            await page.locator('#radio_program_medicare').check();
            await page.locator('#txt_visit_date').fill('25/03/2026');
        });

        // 3. Enter 'This is a test comment for the appointment' in the Comment field
        await test.step('Enter comment in textarea', async () => {
            await page.locator('#txt_comment').fill('This is a test comment for the appointment');
            await expect(page.locator('#txt_comment')).toHaveValue('This is a test comment for the appointment');
        });

        // 4. Click 'Book Appointment' and verify confirmation
        await test.step('Book appointment and verify confirmation', async () => {
            await page.locator('#btn-book-appointment').click();
            await expect(page.locator('h2:has-text("Appointment Confirmation")')).toBeVisible();
            await expect(page.locator('#facility')).toHaveText('Tokyo CURA Healthcare Center');
            await expect(page.locator('#hospital_readmission')).toHaveText('No');
            await expect(page.locator('#program')).toHaveText('Medicare');
            await expect(page.locator('#visit_date')).toHaveText('25/03/2026');
        });
    });
});
