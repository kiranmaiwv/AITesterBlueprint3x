import { Page } from '@playwright/test';
import { CheckoutPage } from '../pages/CheckoutPage';
import { Logger } from '../utils/Logger';

export interface ShippingInfo {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
}

export interface PaymentInfo {
    cardNumber: string;
    expiry: string;
    cvc: string;
    cardHolder: string;
}

export interface OrderResult {
    success: boolean;
    orderNumber?: string;
    errorMessage?: string;
}

export class CheckoutModule {
    private page: Page;
    private checkoutPage: CheckoutPage;
    private logger: Logger;

    constructor(page: Page) {
        this.page = page;
        this.checkoutPage = new CheckoutPage(page);
        this.logger = Logger.create('CheckoutModule');
    }

    /**
     * Navigate to checkout page
     */
    async goToCheckout(): Promise<void> {
        this.logger.step(1, 'Navigate to checkout page');
        await this.checkoutPage.navigate();
        await this.checkoutPage.expectOnCheckoutPage();
        this.logger.info('On checkout page');
    }

    /**
     * Fill in shipping information
     */
    async fillShippingInfo(info: ShippingInfo): Promise<void> {
        this.logger.step(1, 'Filling shipping information');
        
        await this.checkoutPage.enterFirstName(info.firstName);
        await this.checkoutPage.enterLastName(info.lastName);
        await this.checkoutPage.enterEmail(info.email);
        await this.checkoutPage.enterPhone(info.phone);
        await this.checkoutPage.enterAddress(info.address);
        await this.checkoutPage.enterCity(info.city);
        await this.checkoutPage.enterState(info.state);
        await this.checkoutPage.enterZipCode(info.zipCode);
        await this.checkoutPage.selectCountry(info.country);

        this.logger.info('Shipping information filled');
    }

    /**
     * Fill in payment information
     */
    async fillPaymentInfo(payment: PaymentInfo): Promise<void> {
        this.logger.step(1, 'Filling payment information');
        
        await this.checkoutPage.enterCardNumber(payment.cardNumber);
        await this.checkoutPage.enterCardExpiry(payment.expiry);
        await this.checkoutPage.enterCardCvc(payment.cvc);
        await this.checkoutPage.enterCardHolder(payment.cardHolder);

        this.logger.info('Payment information filled');
    }

    /**
     * Apply a promo code
     */
    async applyPromoCode(code: string): Promise<void> {
        this.logger.step(1, `Applying promo code: ${code}`);
        await this.checkoutPage.enterPromoCode(code);
        await this.checkoutPage.clickApplyPromo();
        this.logger.info('Promo code applied');
    }

    /**
     * Complete the checkout process
     */
    async completeCheckout(shipping: ShippingInfo, payment: PaymentInfo): Promise<OrderResult> {
        this.logger.testStart('Complete Checkout');

        try {
            this.logger.step(1, 'Navigate to checkout');
            await this.goToCheckout();

            this.logger.step(2, 'Fill shipping information');
            await this.fillShippingInfo(shipping);

            this.logger.step(3, 'Fill payment information');
            await this.fillPaymentInfo(payment);

            this.logger.step(4, 'Place order');
            await this.checkoutPage.clickPlaceOrder();

            this.logger.step(5, 'Wait for order confirmation');
            await this.checkoutPage.expectOrderConfirmationVisible();

            const orderNumber = await this.checkoutPage.getOrderNumber();
            this.logger.info(`Order placed successfully: ${orderNumber}`);

            this.logger.testEnd('Complete Checkout');
            return { success: true, orderNumber };
        } catch (error) {
            const errorMessage = await this.checkoutPage.getErrorMessage();
            this.logger.error(`Checkout failed: ${errorMessage}`, error);
            
            this.logger.testEnd('Complete Checkout');
            return { success: false, errorMessage };
        }
    }

    /**
     * Get the order total
     */
    async getOrderTotal(): Promise<string> {
        return await this.checkoutPage.getTotal();
    }

    /**
     * Get the order subtotal
     */
    async getOrderSubtotal(): Promise<string> {
        return await this.checkoutPage.getSubtotal();
    }

    /**
     * Get the number of items in cart
     */
    async getCartItemCount(): Promise<number> {
        return await this.checkoutPage.getCartItemCount();
    }

    /**
     * Verify checkout form is complete and ready to submit
     */
    async verifyReadyToPlaceOrder(): Promise<void> {
        await this.checkoutPage.expectPlaceOrderEnabled();
        this.logger.info('Checkout form is valid and ready to submit');
    }

    /**
     * Go back to cart from checkout
     */
    async goBackToCart(): Promise<void> {
        this.logger.step(1, 'Click back to cart');
        await this.checkoutPage.clickBackToCart();
        this.logger.info('Navigated back to cart');
    }
}

