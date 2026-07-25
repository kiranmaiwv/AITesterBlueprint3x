import { ApiHelper, ApiContext } from '../utils/ApiHelper';

export interface LoginResponse {
    token: string;
    userId: string;
    expiresIn: number;
}

export interface UserProfile {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    avatar?: string;
    createdAt: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
}

export interface RegisterResponse {
    userId: string;
    message: string;
}

export class AuthApi {
    private apiHelper: ApiHelper;
    private baseUrl: string;

    constructor(context: ApiContext, baseUrl: string) {
        this.apiHelper = new ApiHelper(context);
        this.baseUrl = baseUrl;
    }

    /**
     * Login via API and get auth token
     */
    async login(username: string, password: string): Promise<LoginResponse> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/auth/login`,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            data: { username, password },
        });

        if (response.status() !== 200) {
            throw new Error(`Login failed: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Register a new user
     */
    async register(userData: RegisterRequest): Promise<RegisterResponse> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/auth/register`,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            data: userData,
        });

        if (response.status() !== 201) {
            throw new Error(`Registration failed: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Get user profile with token
     */
    async getUserProfile(token: string): Promise<UserProfile> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/user/profile`,
            method: 'GET',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to get profile: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Update user profile
     */
    async updateUserProfile(
        token: string,
        profileData: Partial<UserProfile>,
    ): Promise<UserProfile> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/user/profile`,
            method: 'PUT',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            data: profileData,
        });

        if (response.status() !== 200) {
            throw new Error(`Failed to update profile: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Logout and invalidate token
     */
    async logout(token: string): Promise<void> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/auth/logout`,
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status() !== 200 && response.status() !== 204) {
            throw new Error(`Logout failed: ${response.status()}`);
        }
    }

    /**
     * Refresh auth token
     */
    async refreshToken(token: string): Promise<LoginResponse> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/auth/refresh`,
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.status() !== 200) {
            throw new Error(`Token refresh failed: ${response.status()}`);
        }

        return await response.json();
    }

    /**
     * Request password reset
     */
    async requestPasswordReset(email: string): Promise<{ message: string }> {
        const response = await this.apiHelper.callApi({
            url: `${this.baseUrl}/api/auth/password-reset`,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            data: { email },
        });

        if (response.status() !== 200) {
            throw new Error(`Password reset request failed: ${response.status()}`);
        }

        return await response.json();
    }
}

