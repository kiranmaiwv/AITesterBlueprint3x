// spec: cura-make-appointment.test-plan.md
// seed: Lecture_Playwright_AI_Agents/web_vwo/seed.spec.js

import { test, expect } from '../../fixtures/katalon';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';
import curaData from '../../testdata/katalon/cura-data.json';
import { CuraTestData } from '../../testdata/katalon/cura-types';

const data = curaData as CuraTestData;
const { validUser, defaultAppointment } = data;

test.describe('E2E - Successful Make Appointment Flow', () => {
    test('TC-001: Complete end-to-end successful appointment booking', async ({ page }) => {
        const module = new CuraAppointmentModule(page);

        // 1. Navigate to https://katalon-demo-cura.herokuapp.com/
        await test.step('Navigate to CURA Healthcare homepage', async () => {
            await page.goto('https://katalon-demo-cura.herokuapp.com/');
            await expect(page).toHaveTitle(/CURA Healthcare Service/);
            await expect(page.locator('#btn-make-appointment')).toBeVisible();
        });

        // 2. Click the 'Make Appointment' button on the homepage
        await test.step('Click Make Appointment button', async () => {
            await page.locator('#btn-make-appointment').click();
            await expect(page).toHaveURL(/profile\.php#login/);
            await expect(page.locator('#txt-username')).toBeVisible();
            await expect(page.locator('#txt-password')).toBeVisible();
            await expect(page.locator('#btn-login')).toBeVisible();
        });

        // 3. Enter 'John Doe' in the Username field
        await test.step('Enter username', async () => {
            await page.locator('#txt-username').fill(validUser.username);
            await expect(page.locator('#txt-username')).toHaveValue(validUser.username);
        });

        // 4. Enter 'ThisIsNotAPassword' in the Password field
        await test.step('Enter password', async () => {
            await page.locator('#txt-password').fill(validUser.password);
            await expect(page.locator('#txt-password')).toHaveAttribute('type', 'password');
        });

        // 5. Click the 'Login' button
        await test.step('Click Login button and verify appointment form', async () => {
            await page.locator('#btn-login').click();
            await expect(page).toHaveURL(/\/#appointment/);
            await expect(page.locator('#combo_facility')).toBeVisible();
            await expect(page.locator('#chk_hosp498')).toBeVisible();
            await expect(page.locator('#radio_program_medicare')).toBeVisible();
            await expect(page.locator('#txt_visit_date')).toBeVisible();
            await expect(page.locator('#txt_comment')).toBeVisible();
            await expect(page.locator('#btn-book-appointment')).toBeVisible();
        });

        // 6. Select 'Tokyo CURA Healthcare Center' from the Facility dropdown
        await test.step('Select facility', async () => {
            await page.locator('#combo_facility').selectOption(defaultAppointment.facility);
            await expect(page.locator('#combo_facility')).toHaveValue('Tokyo CURA Healthcare Center');
        });

        // 7. Leave the 'Apply for hospital readmission' checkbox unchecked
        await test.step('Verify readmission checkbox is unchecked', async () => {
            await expect(page.locator('#chk_hosp498')).not.toBeChecked();
        });

        // 8. Select the 'Medicare' radio button under Healthcare Program
        await test.step('Select Medicare radio button', async () => {
            await page.locator('#radio_program_medicare').check();
            await expect(page.locator('#radio_program_medicare')).toBeChecked();
            await expect(page.locator('#radio_program_medicaid')).not.toBeChecked();
            await expect(page.locator('#radio_program_none')).not.toBeChecked();
        });

        // 9. Click on the Visit Date input field and enter '25/03/2026'
        await test.step('Enter visit date', async () => {
            await page.locator('#txt_visit_date').fill(defaultAppointment.visitDate);
            await expect(page.locator('#txt_visit_date')).toHaveValue(defaultAppointment.visitDate);
        });

        // 10. Leave the Comment field empty
        await test.step('Verify comment field is empty', async () => {
            await expect(page.locator('#txt_comment')).toHaveValue('');
        });

        // 11. Click the 'Book Appointment' button
        await test.step('Book appointment and verify confirmation', async () => {
            await page.locator('#btn-book-appointment').click();
            await expect(page).toHaveURL(/appointment\.php#summary/);
            await expect(page.locator('h2:has-text("Appointment Confirmation")')).toBeVisible();
            await expect(page.locator('.lead')).toContainText(
                'Please be informed that your appointment has been booked as following:'
            );
            await expect(page.locator('#facility')).toHaveText('Tokyo CURA Healthcare Center');
            await expect(page.locator('#hospital_readmission')).toHaveText('No');
            await expect(page.locator('#program')).toHaveText('Medicare');
            await expect(page.locator('#visit_date')).toHaveText('25/03/2026');
        });
    });
});
