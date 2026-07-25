import { expect, Page } from '@playwright/test';

export class ProductPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // ============================================
    // LOCATORS (as arrow functions)
    // ============================================

    productTitle = () => this.page.locator('[data-testid="product-title"]');
    productPrice = () => this.page.locator('[data-testid="product-price"]');
    productDescription = () => this.page.locator('[data-testid="product-description"]');
    productImage = () => this.page.locator('[data-testid="product-image"]');
    quantityInput = () => this.page.locator('[data-testid="quantity-input"]');
    addToCartButton = () => this.page.locator('[data-testid="add-to-cart"]');
    buyNowButton = () => this.page.locator('[data-testid="buy-now"]');
    productRating = () => this.page.locator('[data-testid="product-rating"]');
    reviewsSection = () => this.page.locator('[data-testid="reviews-section"]');
    reviewCount = () => this.page.locator('[data-testid="review-count"]');
    addReviewButton = () => this.page.locator('[data-testid="add-review"]');
    sizeSelector = () => this.page.locator('[data-testid="size-selector"]');
    colorSelector = () => this.page.locator('[data-testid="color-selector"]');
    stockStatus = () => this.page.locator('[data-testid="stock-status"]');
    wishlistButton = () => this.page.locator('[data-testid="wishlist-button"]');
    shareButton = () => this.page.locator('[data-testid="share-button"]');
    relatedProducts = () => this.page.locator('[data-testid="related-products"]');
    breadcrumb = () => this.page.locator('[data-testid="breadcrumb"]');

    // ============================================
    // ACTIONS (simple, single UI interactions)
    // ============================================

    /**
     * Navigate to a product page by ID
     */
    async navigate(productId: string): Promise<void> {
        await this.page.goto(`/products/${productId}`);
    }

    /**
     * Get the product title text
     */
    async getProductTitle(): Promise<string> {
        return (await this.productTitle().textContent()) || '';
    }

    /**
     * Get the product price
     */
    async getProductPrice(): Promise<string> {
        return (await this.productPrice().textContent()) || '';
    }

    /**
     * Get the product description
     */
    async getProductDescription(): Promise<string> {
        return (await this.productDescription().textContent()) || '';
    }

    /**
     * Set the quantity
     */
    async setQuantity(quantity: number): Promise<void> {
        await this.quantityInput().fill(quantity.toString());
    }

    /**
     * Increment the quantity
     */
    async incrementQuantity(): Promise<void> {
        const currentValue = await this.quantityInput().inputValue();
        await this.quantityInput().fill((parseInt(currentValue) + 1).toString());
    }

    /**
     * Decrement the quantity
     */
    async decrementQuantity(): Promise<void> {
        const currentValue = await this.quantityInput().inputValue();
        const newValue = Math.max(1, parseInt(currentValue) - 1);
        await this.quantityInput().fill(newValue.toString());
    }

    /**
     * Click the add to cart button
     */
    async clickAddToCart(): Promise<void> {
        await this.addToCartButton().click();
    }

    /**
     * Click the buy now button
     */
    async clickBuyNow(): Promise<void> {
        await this.buyNowButton().click();
    }

    /**
     * Select a size
     */
    async selectSize(size: string): Promise<void> {
        await this.sizeSelector().selectOption(size);
    }

    /**
     * Select a color
     */
    async selectColor(color: string): Promise<void> {
        await this.colorSelector().locator(`[data-color="${color}"]`).click();
    }

    /**
     * Click the add to wishlist button
     */
    async clickAddToWishlist(): Promise<void> {
        await this.wishlistButton().click();
    }

    /**
     * Click the share button
     */
    async clickShare(): Promise<void> {
        await this.shareButton().click();
    }

    /**
     * Click the add review button
     */
    async clickAddReview(): Promise<void> {
        await this.addReviewButton().click();
    }

    /**
     * Get the stock status text
     */
    async getStockStatus(): Promise<string> {
        return (await this.stockStatus().textContent()) || '';
    }

    /**
     * Get the product rating value
     */
    async getRating(): Promise<string> {
        return (await this.productRating().textContent()) || '';
    }

    // ============================================
    // ASSERTIONS (inline expectations)
    // ============================================

    async expectProductTitleVisible(): Promise<void> {
        await expect(this.productTitle()).toBeVisible();
    }

    async expectAddToCartEnabled(): Promise<void> {
        await expect(this.addToCartButton()).toBeEnabled();
    }

    async expectAddToCartDisabled(): Promise<void> {
        await expect(this.addToCartButton()).toBeDisabled();
    }

    async expectInStock(): Promise<void> {
        await expect(this.stockStatus()).toContainText(/in stock/i);
    }

    async expectOutOfStock(): Promise<void> {
        await expect(this.stockStatus()).toContainText(/out of stock/i);
    }

    async expectProductImageVisible(): Promise<void> {
        await expect(this.productImage()).toBeVisible();
    }
}

