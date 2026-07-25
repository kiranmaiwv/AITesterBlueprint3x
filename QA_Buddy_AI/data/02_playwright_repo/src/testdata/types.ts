// Type definitions for test data

export interface ValidUser {
    id: string;
    username: string;
    password: string;
    firstName: string;
    lastName: string;
    role: string;
}

export interface InvalidUser {
    username: string;
    password: string;
    expectedError: string;
}

export interface NewUserTemplate {
    username: string;
    password: string;
    firstName: string;
    lastName: string;
}

export interface LockedUser {
    username: string;
    password: string;
    expectedError: string;
}

export interface UsersData {
    validUsers: ValidUser[];
    invalidUsers: InvalidUser[];
    newUserTemplate: NewUserTemplate;
    lockedUser: LockedUser;
}

export interface Product {
    id: string;
    name: string;
    description: string;
    price: number;
    category: string;
    stock: number;
    rating: number;
    sizes?: string[];
    colors?: string[];
}

export interface OutOfStockProduct {
    id: string;
    name: string;
    description: string;
    price: number;
    category: string;
    stock: number;
    rating: number;
}

export interface PromoCode {
    code: string;
    discount: number;
    type: string;
    minOrder: number;
    expired?: boolean;
}

export interface ProductsData {
    products: Product[];
    outOfStockProduct: OutOfStockProduct;
    categories: string[];
    promoCodes: PromoCode[];
}

