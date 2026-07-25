import { test, expect } from '../fixtures';
import { CheckoutModule, ShippingInfo, PaymentInfo } from '../modules/CheckoutModule';
import { ProductModule } from '../modules/ProductModule';
import { LoginModule } from '../modules/LoginModule';
import { config, testData } from '../config';
import productsData from '../testdata/products.json';
import usersData from '../testdata/users.json';
import { UsersData, ProductsData, PromoCode } from '../testdata/types';

const typedUsersData = usersData as UsersData;
const typedProductsData = productsData as ProductsData;

const validUser = typedUsersData.validUsers[0];
const testProduct = typedProductsData.products[0];
const promoCodes: PromoCode[] = typedProductsData.promoCodes;

const shippingInfo: ShippingInfo = {
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@example.com',
    phone: '(555) 123-4567',
    address: testData.addresses.us.street,
    city: testData.addresses.us.city,
    state: testData.addresses.us.state,
    zipCode: testData.addresses.us.zip,
    country: testData.addresses.us.country,
};

const paymentInfo: PaymentInfo = {
    cardNumber: testData.validCreditCard.number,
    expiry: testData.validCreditCard.expiry,
    cvc: testData.validCreditCard.cvc,
    cardHolder: testData.validCreditCard.holder,
};

test.describe('@P0 @Regression @Checkout Checkout Feature', () => {
    let checkoutModule: CheckoutModule;
    let productModule: ProductModule;
    let loginModule: LoginModule;

    test.beforeEach(async ({ page }) => {
        checkoutModule = new CheckoutModule(page);
        productModule = new ProductModule(page);
        loginModule = new LoginModule(page);

        // Login before checkout tests
        await loginModule.doLogin(validUser.username, validUser.password);
    });

    test.describe('@P0 @Smoke Checkout Flow', () => {
        test('should complete checkout successfully', async () => {
            await test.step('Complete full checkout with valid data', async () => {
                await productModule.buyProductNow(testProduct.id);
                const result = await checkoutModule.completeCheckout(shippingInfo, paymentInfo);

                expect(result.success).toBe(true);
                expect(result.orderNumber).toBeTruthy();
            });
        });

        test('should fill shipping information correctly', async () => {
            await test.step('Fill shipping information section', async () => {
                await checkoutModule.goToCheckout();
                await checkoutModule.fillShippingInfo(shippingInfo);
            });
        });

        test('should fill payment information correctly', async () => {
            await test.step('Fill payment information section', async () => {
                await checkoutModule.goToCheckout();
                await checkoutModule.fillPaymentInfo(paymentInfo);
            });
        });
    });

    test.describe('@P1 @Regression Order Summary', () => {
        test('should display correct order total', async () => {
            await test.step('Validate order total on checkout summary', async () => {
                await productModule.buyProductNow(testProduct.id);
                const total = await checkoutModule.getOrderTotal();
                expect(total).toBeTruthy();
            });
        });

        test('should display correct cart item count', async () => {
            await test.step('Validate cart item count in checkout summary', async () => {
                await productModule.buyProductNow(testProduct.id);
                const itemCount = await checkoutModule.getCartItemCount();
                expect(itemCount).toBeGreaterThan(0);
            });
        });
    });

    test.describe('@P1 @Regression Promo Codes', () => {
        test('should apply valid promo code', async () => {
            await test.step('Apply non-expired promo code during checkout', async () => {
                await productModule.buyProductNow(testProduct.id);
                const validPromo = promoCodes.find((p: PromoCode) => !p.expired);
                if (!validPromo) {
                    return;
                }

                await checkoutModule.applyPromoCode(validPromo.code);
            });
        });
    });

    test.describe('@P2 @Regression Navigation', () => {
        test('should navigate back to cart from checkout', async () => {
            await test.step('Return to cart from checkout page', async () => {
                await productModule.buyProductNow(testProduct.id);
                await checkoutModule.goBackToCart();
            });
        });
    });
});

test.describe('@P1 @Regression Checkout - Using Fixtures', () => {
    test('should display checkout page elements', async ({ checkoutPage, page }) => {
        await test.step('Open checkout page and validate critical elements', async () => {
            const loginModule = new LoginModule(page);
            await loginModule.doLogin(validUser.username, validUser.password);
            await checkoutPage.navigate();
            await checkoutPage.expectOnCheckoutPage();
        });
    });

    test('should enable place order button when form is valid', async ({ checkoutModule, page }) => {
        await test.step('Complete form and validate place-order readiness', async () => {
            const loginModule = new LoginModule(page);
            const productModule = new ProductModule(page);
            await loginModule.doLogin(validUser.username, validUser.password);
            await productModule.buyProductNow(testProduct.id);
            await checkoutModule.fillShippingInfo(shippingInfo);
            await checkoutModule.fillPaymentInfo(paymentInfo);
            await checkoutModule.verifyReadyToPlaceOrder();
        });
    });
});

test.describe('@P1 @Regression Checkout - Error Handling', () => {
    test('should show error with invalid payment', async ({ page }) => {
        await test.step('Attempt checkout with invalid card details', async () => {
            const loginModule = new LoginModule(page);
            const productModule = new ProductModule(page);
            const checkoutModule = new CheckoutModule(page);

            await loginModule.doLogin(validUser.username, validUser.password);
            await productModule.buyProductNow(testProduct.id);

            const invalidPayment: PaymentInfo = {
                cardNumber: testData.invalidCreditCard.number,
                expiry: testData.invalidCreditCard.expiry,
                cvc: testData.invalidCreditCard.cvc,
                cardHolder: testData.invalidCreditCard.holder,
            };

            const result = await checkoutModule.completeCheckout(shippingInfo, invalidPayment);

            expect(result.success).toBe(false);
            expect(result.errorMessage).toBeTruthy();
        });
    });
});
