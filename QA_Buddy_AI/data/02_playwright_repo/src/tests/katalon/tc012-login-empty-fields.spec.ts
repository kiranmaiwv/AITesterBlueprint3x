// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-012: Login with empty username and password (negative test)', async ({
        curaHomePage,
        curaLoginPage,
        page,
    }) => {

        // 1. Navigate to login page
        await test.step('Navigate to login page', async () => {
            await curaHomePage.navigate();
            await curaHomePage.clickMakeAppointment();
            await curaLoginPage.expectOnLoginPage();
        });

        // 2. Leave both Username and Password fields empty
        await test.step('Leave both fields empty', async () => {
            await expect(page.locator('#txt-username')).toHaveValue('');
            await expect(page.locator('#txt-password')).toHaveValue('');
        });

        // 3. Click Login and verify error
        await test.step('Click Login and verify failure', async () => {
            await curaLoginPage.clickLogin();
            await curaLoginPage.expectErrorVisible();
            const errorMessage = await curaLoginPage.getErrorMessage();
            expect(errorMessage).toContain('Login failed');
            await expect(page).toHaveURL(/profile\.php#login/);
        });
    });
});
