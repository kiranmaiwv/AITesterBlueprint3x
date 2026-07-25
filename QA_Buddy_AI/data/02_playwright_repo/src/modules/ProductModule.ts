import { Page } from '@playwright/test';
import { ProductPage } from '../pages/ProductPage';
import { HomePage } from '../pages/HomePage';
import { Logger } from '../utils/Logger';

export interface ProductDetails {
    title: string;
    price: string;
    description: string;
    rating: string;
    stockStatus: string;
}

export interface AddToCartOptions {
    quantity?: number;
    size?: string;
    color?: string;
}

export class ProductModule {
    private page: Page;
    private productPage: ProductPage;
    private homePage: HomePage;
    private logger: Logger;

    constructor(page: Page) {
        this.page = page;
        this.productPage = new ProductPage(page);
        this.homePage = new HomePage(page);
        this.logger = Logger.create('ProductModule');
    }

    /**
     * Navigate to a product and get its details
     */
    async getProductDetails(productId: string): Promise<ProductDetails> {
        this.logger.step(1, `Navigate to product: ${productId}`);
        await this.productPage.navigate(productId);

        this.logger.step(2, 'Extract product details');
        const details: ProductDetails = {
            title: await this.productPage.getProductTitle(),
            price: await this.productPage.getProductPrice(),
            description: await this.productPage.getProductDescription(),
            rating: await this.productPage.getRating(),
            stockStatus: await this.productPage.getStockStatus(),
        };

        this.logger.info(`Retrieved details for product: ${details.title}`);
        return details;
    }

    /**
     * Add a product to cart with optional configuration
     */
    async addProductToCart(productId: string, options?: AddToCartOptions): Promise<void> {
        this.logger.step(1, `Navigate to product: ${productId}`);
        await this.productPage.navigate(productId);

        if (options?.size) {
            this.logger.step(2, `Select size: ${options.size}`);
            await this.productPage.selectSize(options.size);
        }

        if (options?.color) {
            this.logger.step(3, `Select color: ${options.color}`);
            await this.productPage.selectColor(options.color);
        }

        if (options?.quantity && options.quantity > 1) {
            this.logger.step(4, `Set quantity: ${options.quantity}`);
            await this.productPage.setQuantity(options.quantity);
        }

        this.logger.step(5, 'Click add to cart');
        await this.productPage.clickAddToCart();

        this.logger.info('Product added to cart successfully');
    }

    /**
     * Buy a product immediately with optional configuration
     */
    async buyProductNow(productId: string, options?: AddToCartOptions): Promise<void> {
        this.logger.step(1, `Navigate to product: ${productId}`);
        await this.productPage.navigate(productId);

        if (options?.size) {
            this.logger.step(2, `Select size: ${options.size}`);
            await this.productPage.selectSize(options.size);
        }

        if (options?.color) {
            this.logger.step(3, `Select color: ${options.color}`);
            await this.productPage.selectColor(options.color);
        }

        if (options?.quantity && options.quantity > 1) {
            this.logger.step(4, `Set quantity: ${options.quantity}`);
            await this.productPage.setQuantity(options.quantity);
        }

        this.logger.step(5, 'Click buy now');
        await this.productPage.clickBuyNow();

        this.logger.step(6, 'Wait for checkout page');
        await this.page.waitForURL('**/checkout');

        this.logger.info('Redirected to checkout page');
    }

    /**
     * Add a product to wishlist
     */
    async addProductToWishlist(productId: string): Promise<void> {
        this.logger.step(1, `Navigate to product: ${productId}`);
        await this.productPage.navigate(productId);

        this.logger.step(2, 'Click add to wishlist');
        await this.productPage.clickAddToWishlist();

        this.logger.info('Product added to wishlist');
    }

    /**
     * Search for products from home page
     */
    async searchProducts(searchTerm: string): Promise<void> {
        this.logger.step(1, 'Navigate to home page');
        await this.homePage.navigate();

        this.logger.step(2, `Enter search term: ${searchTerm}`);
        await this.homePage.enterSearchText(searchTerm);

        this.logger.step(3, 'Click search button');
        await this.homePage.clickSearch();

        this.logger.info(`Searched for: ${searchTerm}`);
    }

    /**
     * Verify product is in stock
     */
    async verifyProductInStock(productId: string): Promise<boolean> {
        this.logger.step(1, `Navigate to product: ${productId}`);
        await this.productPage.navigate(productId);

        const stockStatus = await this.productPage.getStockStatus();
        const inStock = stockStatus.toLowerCase().includes('in stock');

        this.logger.info(`Product ${productId} is ${inStock ? 'in stock' : 'out of stock'}`);
        return inStock;
    }

    /**
     * Verify add to cart is available for a product
     */
    async verifyCanAddToCart(productId: string): Promise<void> {
        await this.productPage.navigate(productId);
        await this.productPage.expectAddToCartEnabled();
        this.logger.info('Add to cart is available');
    }
}

