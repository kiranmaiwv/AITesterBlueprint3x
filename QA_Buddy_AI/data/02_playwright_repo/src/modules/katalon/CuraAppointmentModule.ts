import { Page } from '@playwright/test';
import { CuraHomePage } from '../../pages/katalon/CuraHomePage';
import { CuraLoginPage } from '../../pages/katalon/CuraLoginPage';
import { CuraAppointmentPage } from '../../pages/katalon/CuraAppointmentPage';
import { CuraConfirmationPage } from '../../pages/katalon/CuraConfirmationPage';
import { Logger } from '../../utils/Logger';

export interface AppointmentData {
    facility: string;
    readmission: boolean;
    program: 'Medicare' | 'Medicaid' | 'None';
    visitDate: string;
    comment?: string;
}

export class CuraAppointmentModule {
    private page: Page;
    private homePage: CuraHomePage;
    private loginPage: CuraLoginPage;
    private appointmentPage: CuraAppointmentPage;
    private confirmationPage: CuraConfirmationPage;
    private logger: Logger;

    constructor(page: Page) {
        this.page = page;
        this.homePage = new CuraHomePage(page);
        this.loginPage = new CuraLoginPage(page);
        this.appointmentPage = new CuraAppointmentPage(page);
        this.confirmationPage = new CuraConfirmationPage(page);
        this.logger = Logger.create('CuraAppointmentModule');
    }

    /**
     * Navigate to the homepage and click Make Appointment to reach login page
     */
    async goToLogin(): Promise<void> {
        this.logger.step(1, 'Navigate to CURA Healthcare homepage');
        await this.homePage.navigate();

        this.logger.step(2, 'Click Make Appointment button');
        await this.homePage.clickMakeAppointment();

        this.logger.step(3, 'Verify login page is displayed');
        await this.loginPage.expectOnLoginPage();
        this.logger.info('Navigated to login page');
    }

    /**
     * Perform login with provided credentials
     */
    async doLogin(username: string, password: string): Promise<void> {
        this.logger.step(1, 'Enter username');
        await this.loginPage.enterUsername(username);

        this.logger.step(2, 'Enter password');
        await this.loginPage.enterPassword(password);

        this.logger.step(3, 'Click login button');
        await this.loginPage.clickLogin();

        this.logger.info('Login submitted');
    }

    /**
     * Attempt invalid login and return error message
     */
    async attemptInvalidLogin(username: string, password: string): Promise<string> {
        this.logger.step(1, 'Enter invalid username');
        await this.loginPage.enterUsername(username);

        this.logger.step(2, 'Enter invalid password');
        await this.loginPage.enterPassword(password);

        this.logger.step(3, 'Click login button');
        await this.loginPage.clickLogin();

        this.logger.step(4, 'Wait for error message');
        await this.loginPage.expectErrorVisible();

        const errorMessage = await this.loginPage.getErrorMessage();
        this.logger.info(`Login failed with message: ${errorMessage}`);
        return errorMessage;
    }

    /**
     * Navigate from homepage → login → appointment page with valid credentials
     */
    async navigateToAppointmentForm(username: string, password: string): Promise<void> {
        await this.goToLogin();
        await this.doLogin(username, password);

        this.logger.step(4, 'Verify appointment form is displayed');
        await this.appointmentPage.expectOnAppointmentPage();
        this.logger.info('On appointment form page');
    }

    /**
     * Fill and submit the appointment form
     */
    async fillAndSubmitAppointment(data: AppointmentData): Promise<void> {
        this.logger.step(1, `Select facility: ${data.facility}`);
        await this.appointmentPage.selectFacility(data.facility);

        if (data.readmission) {
            this.logger.step(2, 'Check hospital readmission checkbox');
            await this.appointmentPage.checkReadmission();
        } else {
            this.logger.step(2, 'Leave hospital readmission unchecked');
        }

        this.logger.step(3, `Select healthcare program: ${data.program}`);
        switch (data.program) {
            case 'Medicare':
                await this.appointmentPage.selectMedicare();
                break;
            case 'Medicaid':
                await this.appointmentPage.selectMedicaid();
                break;
            case 'None':
                await this.appointmentPage.selectNone();
                break;
        }

        this.logger.step(4, `Enter visit date: ${data.visitDate}`);
        await this.appointmentPage.enterVisitDate(data.visitDate);

        if (data.comment) {
            this.logger.step(5, `Enter comment: ${data.comment}`);
            await this.appointmentPage.enterComment(data.comment);
        }

        this.logger.step(6, 'Click Book Appointment button');
        await this.appointmentPage.clickBookAppointment();

        this.logger.info('Appointment form submitted');
    }

    /**
     * Verify confirmation page shows expected values
     */
    async verifyConfirmation(data: AppointmentData): Promise<void> {
        this.logger.step(1, 'Verify on confirmation page');
        await this.confirmationPage.expectOnConfirmationPage();

        this.logger.step(2, 'Verify confirmation message');
        await this.confirmationPage.expectConfirmationMessage();

        this.logger.step(3, 'Verify facility');
        await this.confirmationPage.expectFacility(data.facility);

        this.logger.step(4, 'Verify readmission');
        await this.confirmationPage.expectReadmission(data.readmission ? 'Yes' : 'No');

        this.logger.step(5, 'Verify healthcare program');
        await this.confirmationPage.expectProgram(data.program);

        this.logger.step(6, 'Verify visit date');
        await this.confirmationPage.expectVisitDate(data.visitDate);

        this.logger.info('Confirmation page verified successfully');
    }

    /**
     * Complete end-to-end appointment flow: navigate → login → fill → submit → verify
     */
    async completeAppointmentFlow(
        username: string,
        password: string,
        data: AppointmentData,
    ): Promise<void> {
        await this.navigateToAppointmentForm(username, password);
        await this.fillAndSubmitAppointment(data);
        await this.verifyConfirmation(data);
    }
}
