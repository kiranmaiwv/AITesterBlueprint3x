// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-007: Book appointment with Seoul CURA Healthcare Center', async ({ page }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to appointment form via login
        await test.step('Navigate to appointment form', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
        });

        // 2. Select 'Seoul CURA Healthcare Center' from the Facility dropdown
        await test.step('Select Seoul CURA Healthcare Center', async () => {
            await page.locator('#combo_facility').selectOption('Seoul CURA Healthcare Center');
            await expect(page.locator('#combo_facility')).toHaveValue('Seoul CURA Healthcare Center');
        });

        // 3. Leave readmission unchecked, select 'None' for Healthcare Program, enter date
        await test.step('Fill remaining form fields', async () => {
            await expect(page.locator('#chk_hosp498')).not.toBeChecked();
            await page.locator('#radio_program_none').check();
            await expect(page.locator('#radio_program_none')).toBeChecked();
            await page.locator('#txt_visit_date').fill('25/03/2026');
        });

        // 4. Click 'Book Appointment' and verify confirmation
        await test.step('Book appointment and verify confirmation', async () => {
            await page.locator('#btn-book-appointment').click();
            await expect(page.locator('h2:has-text("Appointment Confirmation")')).toBeVisible();
            await expect(page.locator('#facility')).toHaveText('Seoul CURA Healthcare Center');
            await expect(page.locator('#program')).toHaveText('None');
            await expect(page.locator('#hospital_readmission')).toHaveText('No');
            await expect(page.locator('#visit_date')).toHaveText('25/03/2026');
        });
    });
});
