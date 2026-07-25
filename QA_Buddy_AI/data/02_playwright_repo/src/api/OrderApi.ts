import { ApiHelper, ApiContext } from '../utils/ApiHelper';

export interface OrderItem {
    productId: string;
    productName: string;
    quantity: number;
    price: number;
}

export interface ShippingAddress {
    firstName: string;
    lastName: string;
    address: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
    phone: string;
}

export interface Order {
    id: string;
    userId: string;
    items: OrderItem[];
    shippingAddress: ShippingAddress;
    subtotal: number;
    shipping: number;
    tax: number;
    total: number;
    status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
    createdAt: string;
    updatedAt: string;
}

export interface CreateOrderRequest {
    items: { productId: string; quantity: number }[];
    shippingAddress: ShippingAddress;
    paymentMethodId: string;
    promoCode?: string;
}

export interface OrderListResponse {
    orders: Order[];
    total: number;
    page: number;
    pageSize: number;
}

export class OrderApi {
    private apiHelper: ApiHelper;
    private baseUrl: string;

    constructor(context: ApiContext, baseUrl: string) {
        this.apiHelper = new ApiHelper(context);
        this.baseUrl = baseUrl;
    }

    /**
     * Create a new order
     */
    async createOrder(token: string, orderData: CreateOrderRequest): Promise<Order> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/orders`,
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            data: orderData,
        });

        if (response.status() !== 201) {
            throw new Error(`Failed to create order: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Get an order by ID
     */
    async getOrder(token: string, orderId: string): Promise<Order> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/orders/${orderId}`,
            method: 'GET',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get order: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Get all orders for current user
     */
    async getOrders(token: string, page: number = 1, pageSize: number = 10): Promise<OrderListResponse> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/orders`,
            method: 'GET',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            params: {
                page: page.toString(),
                pageSize: pageSize.toString(),
            },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get orders: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Cancel an order
     */
    async cancelOrder(token: string, orderId: string): Promise<Order> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/orders/${orderId}/cancel`,
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to cancel order: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Get order status with polling for updates
     */
    async waitForOrderStatus(
        token: string,
        orderId: string,
        expectedStatus: Order['status'],
        maxAttempts: number = 10,
        intervalMs: number = 2000,
    ): Promise<Order> {
        const response = await this.apiHelper.callApiWithRetry(
            {
                url: `${this.baseUrl}/api/orders/${orderId}`,
                method: 'GET',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            },
            {
                condition: async (res) => {
                    const order = await res.json();
                    return order.status === expectedStatus;
                },
                retryCount: maxAttempts,
                pollingInterval: intervalMs,
            },
        );

        return await response.json();
    }

    /**
     * Validate promo code
     */
    async validatePromoCode(
        token: string,
        code: string,
    ): Promise<{ valid: boolean; discount: number; message: string }> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/orders/promo/validate`,
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            data: { code },
        });

        return await response.json();
    }
}

