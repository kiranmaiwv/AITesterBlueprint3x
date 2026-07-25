// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-011: Login with invalid credentials (negative test)', async ({
        curaHomePage,
        curaLoginPage,
        page,
    }) => {
        const invalidUser = data.invalidUsers[0];

        // 1. Navigate to login page
        await test.step('Navigate to login page', async () => {
            await curaHomePage.navigate();
            await curaHomePage.clickMakeAppointment();
            await curaLoginPage.expectOnLoginPage();
        });

        // 2. Enter invalid credentials
        await test.step('Enter invalid credentials', async () => {
            await curaLoginPage.enterUsername(invalidUser.username);
            await curaLoginPage.enterPassword(invalidUser.password);
        });

        // 3. Click Login and verify error
        await test.step('Click Login and verify error message', async () => {
            await curaLoginPage.clickLogin();
            await curaLoginPage.expectErrorVisible();
            const errorMessage = await curaLoginPage.getErrorMessage();
            expect(errorMessage).toContain(invalidUser.expectedError);
            await expect(page).toHaveURL(/profile\.php#login/);
        });
    });
});
