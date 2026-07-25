import { expect, Page } from '@playwright/test';

export class CheckoutPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    // Shipping Information
    firstNameInput = () => this.page.locator('#firstName');
    lastNameInput = () => this.page.locator('#lastName');
    emailInput = () => this.page.locator('#email');
    phoneInput = () => this.page.locator('#phone');
    addressInput = () => this.page.locator('#address');
    cityInput = () => this.page.locator('#city');
    stateInput = () => this.page.locator('#state');
    zipCodeInput = () => this.page.locator('#zipCode');
    countrySelect = () => this.page.locator('#country');

    // Payment Information
    cardNumberInput = () => this.page.locator('#cardNumber');
    cardExpiryInput = () => this.page.locator('#cardExpiry');
    cardCvcInput = () => this.page.locator('#cardCvc');
    cardHolderInput = () => this.page.locator('#cardHolder');

    // Order Summary
    orderSummary = () => this.page.locator('[data-testid="order-summary"]');
    subtotal = () => this.page.locator('[data-testid="subtotal"]');
    shipping = () => this.page.locator('[data-testid="shipping-cost"]');
    tax = () => this.page.locator('[data-testid="tax"]');
    total = () => this.page.locator('[data-testid="total"]');
    cartItems = () => this.page.locator('[data-testid="cart-item"]');

    // Buttons
    placeOrderButton = () => this.page.locator('[data-testid="place-order"]');
    backToCartButton = () => this.page.locator('[data-testid="back-to-cart"]');
    applyPromoButton = () => this.page.locator('[data-testid="apply-promo"]');
    promoCodeInput = () => this.page.locator('#promoCode');

    // Messages
    errorMessage = () => this.page.locator('[data-testid="error-message"]');
    successMessage = () => this.page.locator('[data-testid="success-message"]');
    orderConfirmation = () => this.page.locator('[data-testid="order-confirmation"]');
    orderNumber = () => this.page.locator('[data-testid="order-number"]');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    async navigate(): Promise<void> {
        await this.page.goto('/checkout');
    }

    async enterFirstName(name: string): Promise<void> {
        await this.firstNameInput().fill(name);
    }

    async enterLastName(name: string): Promise<void> {
        await this.lastNameInput().fill(name);
    }

    async enterEmail(email: string): Promise<void> {
        await this.emailInput().fill(email);
    }

    async enterPhone(phone: string): Promise<void> {
        await this.phoneInput().fill(phone);
    }

    async enterAddress(address: string): Promise<void> {
        await this.addressInput().fill(address);
    }

    async enterCity(city: string): Promise<void> {
        await this.cityInput().fill(city);
    }

    async enterState(state: string): Promise<void> {
        await this.stateInput().fill(state);
    }

    async enterZipCode(zip: string): Promise<void> {
        await this.zipCodeInput().fill(zip);
    }

    async selectCountry(country: string): Promise<void> {
        await this.countrySelect().selectOption(country);
    }

    async enterCardNumber(cardNumber: string): Promise<void> {
        await this.cardNumberInput().fill(cardNumber);
    }

    async enterCardExpiry(expiry: string): Promise<void> {
        await this.cardExpiryInput().fill(expiry);
    }

    async enterCardCvc(cvc: string): Promise<void> {
        await this.cardCvcInput().fill(cvc);
    }

    async enterCardHolder(name: string): Promise<void> {
        await this.cardHolderInput().fill(name);
    }

    async clickPlaceOrder(): Promise<void> {
        await this.placeOrderButton().click();
    }

    async clickBackToCart(): Promise<void> {
        await this.backToCartButton().click();
    }

    async enterPromoCode(code: string): Promise<void> {
        await this.promoCodeInput().fill(code);
    }

    async clickApplyPromo(): Promise<void> {
        await this.applyPromoButton().click();
    }

    async getTotal(): Promise<string> {
        return (await this.total().textContent()) || '';
    }

    async getSubtotal(): Promise<string> {
        return (await this.subtotal().textContent()) || '';
    }

    async getOrderNumber(): Promise<string> {
        return (await this.orderNumber().textContent()) || '';
    }

    async getErrorMessage(): Promise<string> {
        return (await this.errorMessage().textContent()) || '';
    }

    async getCartItemCount(): Promise<number> {
        return await this.cartItems().count();
    }

    // ============================================
    // ASSERTIONS (inline expectations)
    // ============================================

    async expectOnCheckoutPage(): Promise<void> {
        await expect(this.page).toHaveURL(/.*checkout.*/);
    }

    async expectOrderConfirmationVisible(): Promise<void> {
        await expect(this.orderConfirmation()).toBeVisible();
    }

    async expectErrorVisible(): Promise<void> {
        await expect(this.errorMessage()).toBeVisible();
    }

    async expectPlaceOrderEnabled(): Promise<void> {
        await expect(this.placeOrderButton()).toBeEnabled();
    }

    async expectPlaceOrderDisabled(): Promise<void> {
        await expect(this.placeOrderButton()).toBeDisabled();
    }

    async expectSuccessMessageVisible(): Promise<void> {
        await expect(this.successMessage()).toBeVisible();
    }
}

