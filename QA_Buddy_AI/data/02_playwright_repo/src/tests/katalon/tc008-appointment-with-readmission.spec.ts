// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-008: Book appointment with hospital readmission checked', async ({ page }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to appointment form via login
        await test.step('Navigate to appointment form', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
        });

        // 2. Select 'Tokyo CURA Healthcare Center' from the Facility dropdown
        await test.step('Select Tokyo CURA Healthcare Center', async () => {
            await page.locator('#combo_facility').selectOption('Tokyo CURA Healthcare Center');
        });

        // 3. Check the 'Apply for hospital readmission' checkbox
        await test.step('Check readmission checkbox', async () => {
            await page.locator('#chk_hosp498').check();
            await expect(page.locator('#chk_hosp498')).toBeChecked();
        });

        // 4. Select the 'Medicare' radio button and enter date '25/03/2026'
        await test.step('Select Medicare and enter visit date', async () => {
            await page.locator('#radio_program_medicare').check();
            await expect(page.locator('#radio_program_medicare')).toBeChecked();
            await page.locator('#txt_visit_date').fill('25/03/2026');
        });

        // 5. Click 'Book Appointment' and verify confirmation
        await test.step('Book appointment and verify confirmation', async () => {
            await page.locator('#btn-book-appointment').click();
            await expect(page.locator('h2:has-text("Appointment Confirmation")')).toBeVisible();
            await expect(page.locator('#facility')).toHaveText('Tokyo CURA Healthcare Center');
            await expect(page.locator('#hospital_readmission')).toHaveText('Yes');
            await expect(page.locator('#program')).toHaveText('Medicare');
            await expect(page.locator('#visit_date')).toHaveText('25/03/2026');
        });
    });
});
