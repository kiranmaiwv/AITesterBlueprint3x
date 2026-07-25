// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-003: Verify login page elements and labels', async ({ curaHomePage, curaLoginPage }) => {

        // 1. Navigate to https://katalon-demo-cura.herokuapp.com/ and click 'Make Appointment'
        await test.step('Navigate to login page', async () => {
            await curaHomePage.navigate();
            await curaHomePage.clickMakeAppointment();
            await curaLoginPage.expectOnLoginPage();
        });

        // 2. Inspect the login form elements
        await test.step('Verify login form elements', async () => {
            await curaLoginPage.expectUsernameFieldVisible();
            await curaLoginPage.expectPasswordFieldVisible();
            await curaLoginPage.expectLoginButtonVisible();
            await curaLoginPage.expectPasswordFieldMasked();
        });
    });
});
