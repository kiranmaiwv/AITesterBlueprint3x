import { test as base } from '@playwright/test';
import { CuraHomePage } from '../../pages/katalon/CuraHomePage';
import { CuraLoginPage } from '../../pages/katalon/CuraLoginPage';
import { CuraAppointmentPage } from '../../pages/katalon/CuraAppointmentPage';
import { CuraConfirmationPage } from '../../pages/katalon/CuraConfirmationPage';
import { CuraAppointmentModule } from '../../modules/katalon/CuraAppointmentModule';

export type CuraTestFixtures = {
    curaHomePage: CuraHomePage;
    curaLoginPage: CuraLoginPage;
    curaAppointmentPage: CuraAppointmentPage;
    curaConfirmationPage: CuraConfirmationPage;
    curaAppointmentModule: CuraAppointmentModule;
};

export const test = base.extend<CuraTestFixtures>({
    curaHomePage: async ({ page }, use) => {
        await use(new CuraHomePage(page));
    },

    curaLoginPage: async ({ page }, use) => {
        await use(new CuraLoginPage(page));
    },

    curaAppointmentPage: async ({ page }, use) => {
        await use(new CuraAppointmentPage(page));
    },

    curaConfirmationPage: async ({ page }, use) => {
        await use(new CuraConfirmationPage(page));
    },

    curaAppointmentModule: async ({ page }, use) => {
        await use(new CuraAppointmentModule(page));
    },
});

export { expect } from '@playwright/test';
