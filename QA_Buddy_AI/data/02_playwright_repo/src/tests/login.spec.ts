import { test, expect } from '../fixtures';
import { LoginModule } from '../modules/LoginModule';
import usersData from '../testdata/users.json';
import { UsersData, InvalidUser } from '../testdata/types';

const typedUsersData = usersData as UsersData;
const validUser = typedUsersData.validUsers[0];
const invalidUsers: InvalidUser[] = typedUsersData.invalidUsers;

test.describe('@P1 @Regression @Login Login Feature', () => {
    let loginModule: LoginModule;

    test.beforeEach(async ({ page }) => {
        loginModule = new LoginModule(page);
    });

    test.describe('@P0 @Smoke Valid Login Scenarios', () => {
        test('should login successfully with valid credentials', async ({ page }) => {
            await test.step('Login and validate home redirection', async () => {
                await loginModule.doLogin(validUser.username, validUser.password);
                await loginModule.verifyLoggedIn();
                expect(page.url()).toContain('/home');
            });
        });

        test('should login with remember me option', async ({ page }) => {
            await test.step('Login with remember me enabled and validate', async () => {
                await loginModule.doLoginWithRememberMe(validUser.username, validUser.password);
                await loginModule.verifyLoggedIn();
                expect(page.url()).toContain('/home');
            });
        });

        test('should logout successfully', async ({ page }) => {
            await test.step('Login, logout, and validate session end', async () => {
                await loginModule.doLogin(validUser.username, validUser.password);
                await loginModule.verifyLoggedIn();
                await loginModule.doLogout();
                await loginModule.verifyLoggedOut();
                expect(page.url()).toContain('/login');
            });
        });
    });

    test.describe('@P1 @Regression Invalid Login Scenarios', () => {
        test('should show error with invalid credentials', async () => {
            await test.step('Attempt invalid login and validate error', async () => {
                const invalidUser = invalidUsers[0];
                const errorMessage = await loginModule.attemptInvalidLogin(
                    invalidUser.username,
                    invalidUser.password,
                );

                expect(errorMessage).toContain(invalidUser.expectedError);
            });
        });

        test('should show error when username is empty', async () => {
            await test.step('Attempt login with empty username', async () => {
                const emptyUsername = invalidUsers.find((u: InvalidUser) => u.username === '');
                if (!emptyUsername) {
                    return;
                }

                const errorMessage = await loginModule.attemptInvalidLogin(
                    emptyUsername.username,
                    emptyUsername.password,
                );
                expect(errorMessage).toContain(emptyUsername.expectedError);
            });
        });

        test('should show error when password is empty', async () => {
            await test.step('Attempt login with empty password', async () => {
                const emptyPassword = invalidUsers.find((u: InvalidUser) => u.password === '');
                if (!emptyPassword) {
                    return;
                }

                const errorMessage = await loginModule.attemptInvalidLogin(
                    emptyPassword.username,
                    emptyPassword.password,
                );
                expect(errorMessage).toContain(emptyPassword.expectedError);
            });
        });
    });

    test.describe('@P2 @Regression Login Page Elements', () => {
        test('should display login form elements', async ({ loginPage }) => {
            await test.step('Validate login form controls are visible', async () => {
                await loginPage.navigate();
                await loginPage.expectUsernameFieldVisible();
                await loginPage.expectPasswordFieldVisible();
                await loginPage.expectLoginButtonEnabled();
            });
        });

        test('should navigate to forgot password page', async () => {
            await test.step('Navigate to forgot password page', async () => {
                await loginModule.goToForgotPassword();
            });
        });

        test('should navigate to sign up page', async () => {
            await test.step('Navigate to sign up page', async () => {
                await loginModule.goToSignUp();
            });
        });
    });
});

test.describe('@P0 @Smoke @Login Login - Using Fixtures', () => {
    test('should show user avatar when logged in', async ({ authenticatedPage }) => {
        await test.step('Validate avatar on authenticated page', async () => {
            const userAvatar = authenticatedPage.locator('[data-testid="user-avatar"]');
            await expect(userAvatar).toBeVisible();
        });
    });

    test('should display correct username after login', async ({ authenticatedPage }) => {
        await test.step('Validate username display on authenticated page', async () => {
            const usernameDisplay = authenticatedPage.locator('[data-testid="username-display"]');
            await expect(usernameDisplay).toBeVisible();
        });
    });
});
