// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-015: Verify each Healthcare Program radio button selection', async ({
        page,
        curaAppointmentPage,
    }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to the Make Appointment form (after login)
        await test.step('Navigate to appointment form', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
            await expect(page.locator('#radio_program_medicare')).toBeVisible();
            await expect(page.locator('#radio_program_medicaid')).toBeVisible();
            await expect(page.locator('#radio_program_none')).toBeVisible();
        });

        // 2. Click the 'Medicare' radio button
        await test.step('Select Medicare and verify state', async () => {
            await curaAppointmentPage.selectMedicare();
            await curaAppointmentPage.expectMedicareSelected();
            await expect(page.locator('#radio_program_medicaid')).not.toBeChecked();
            await expect(page.locator('#radio_program_none')).not.toBeChecked();
        });

        // 3. Click the 'Medicaid' radio button
        await test.step('Select Medicaid and verify state', async () => {
            await curaAppointmentPage.selectMedicaid();
            await curaAppointmentPage.expectMedicaidSelected();
            await expect(page.locator('#radio_program_medicare')).not.toBeChecked();
            await expect(page.locator('#radio_program_none')).not.toBeChecked();
        });

        // 4. Click the 'None' radio button
        await test.step('Select None and verify state', async () => {
            await curaAppointmentPage.selectNone();
            await curaAppointmentPage.expectNoneSelected();
            await expect(page.locator('#radio_program_medicare')).not.toBeChecked();
            await expect(page.locator('#radio_program_medicaid')).not.toBeChecked();
        });
    });
});
