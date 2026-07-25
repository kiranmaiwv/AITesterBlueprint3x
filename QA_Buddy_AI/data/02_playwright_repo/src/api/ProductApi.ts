import { ApiHelper, ApiContext } from '../utils/ApiHelper';

export interface Product {
    id: string;
    name: string;
    description: string;
    price: number;
    category: string;
    stock: number;
    images: string[];
    rating: number;
    reviewCount: number;
}

export interface ProductListResponse {
    products: Product[];
    total: number;
    page: number;
    pageSize: number;
}

export interface ProductSearchParams {
    query?: string;
    category?: string;
    minPrice?: number;
    maxPrice?: number;
    page?: number;
    pageSize?: number;
    sortBy?: 'price' | 'rating' | 'name' | 'createdAt';
    sortOrder?: 'asc' | 'desc';
}

export interface Review {
    id: string;
    userId: string;
    userName: string;
    rating: number;
    comment: string;
    createdAt: string;
}

export class ProductApi {
    private apiHelper: ApiHelper;
    private baseUrl: string;

    constructor(context: ApiContext, baseUrl: string) {
        this.apiHelper = new ApiHelper(context);
        this.baseUrl = baseUrl;
    }

    /**
     * Get a product by ID
     */
    async getProduct(productId: string): Promise<Product> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/products/${productId}`,
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get product: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Get all products with optional filters
     */
    async getProducts(params?: ProductSearchParams): Promise<ProductListResponse> {
        const queryParams: Record<string, string> = {};
        
        if (params?.query) queryParams.query = params.query;
        if (params?.category) queryParams.category = params.category;
        if (params?.minPrice) queryParams.minPrice = params.minPrice.toString();
        if (params?.maxPrice) queryParams.maxPrice = params.maxPrice.toString();
        if (params?.page) queryParams.page = params.page.toString();
        if (params?.pageSize) queryParams.pageSize = params.pageSize.toString();
        if (params?.sortBy) queryParams.sortBy = params.sortBy;
        if (params?.sortOrder) queryParams.sortOrder = params.sortOrder;

        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/products`,
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            params: queryParams,
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get products: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Search products by query
     */
    async searchProducts(query: string, page: number = 1): Promise<ProductListResponse> {
        return this.getProducts({ query, page });
    }

    /**
     * Get products by category
     */
    async getProductsByCategory(category: string, page: number = 1): Promise<ProductListResponse> {
        return this.getProducts({ category, page });
    }

    /**
     * Get product reviews
     */
    async getProductReviews(productId: string): Promise<Review[]> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/products/${productId}/reviews`,
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get reviews: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Add a product review
     */
    async addProductReview(
        token: string,
        productId: string,
        rating: number,
        comment: string,
    ): Promise<Review> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/products/${productId}/reviews`,
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            data: { rating, comment },
        });

        if (response.status() !== 201) {
            throw new Error(`Failed to add review: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Get featured products
     */
    async getFeaturedProducts(): Promise<Product[]> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/products/featured`,
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get featured products: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Check product stock availability
     */
    async checkStock(productId: string): Promise<{ available: boolean; quantity: number }> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/products/${productId}/stock`,
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to check stock: ${response.status()}`);
        }

        return await response.json();
    }
}

