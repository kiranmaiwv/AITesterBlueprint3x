// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-002: Verify homepage elements before making appointment', async ({ curaHomePage }) => {

        // 1. Navigate to https://katalon-demo-cura.herokuapp.com/
        await test.step('Navigate to homepage and verify elements', async () => {
            await curaHomePage.navigate();
            await curaHomePage.expectPageLoaded();
            await curaHomePage.expectBrandHeadingVisible();
            await curaHomePage.expectMakeAppointmentButtonVisible();
            await curaHomePage.expectToggleNavigationVisible();
        });

        // 2. Click the hamburger menu icon (toggle navigation)
        await test.step('Click hamburger menu and verify sidebar', async () => {
            await curaHomePage.clickToggleNavigation();
            await curaHomePage.expectSidebarMenuVisible();
            await curaHomePage.expectSidebarMenuItems();
        });
    });
});
