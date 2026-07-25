// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-014: Navigate back to homepage from confirmation page', async ({
        page,
        curaHomePage,
        curaConfirmationPage,
    }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Complete the full appointment booking flow
        await test.step('Complete appointment booking to reach confirmation', async () => {
            await module.navigateToAppointmentForm(validUser.username, validUser.password);
            await page.locator('#combo_facility').selectOption('Tokyo CURA Healthcare Center');
            await page.locator('#radio_program_medicare').check();
            await page.locator('#txt_visit_date').fill('25/03/2026');
            await page.locator('#btn-book-appointment').click();
            await curaConfirmationPage.expectOnConfirmationPage();
        });

        // 2. Click 'Go to Homepage' link and verify navigation
        await test.step('Navigate back to homepage', async () => {
            await curaHomePage.clickToggleNavigation();
            await curaHomePage.clickSidebarHome();
            await curaHomePage.expectPageLoaded();
            await curaHomePage.expectMakeAppointmentButtonVisible();
        });
    });
});
