/**
 * Utility class for generating random test data
 */
export class DataGenerator {
    private static readonly CHARS_LOWER = 'abcdefghijklmnopqrstuvwxyz';
    private static readonly CHARS_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    private static readonly CHARS_NUMERIC = '0123456789';
    private static readonly CHARS_SPECIAL = '!@#$%^&*()_+-=[]{}|;:,.<>?';

    /**
     * Generate a random string of specified length
     */
    static randomString(length: number, charset?: string): string {
        const chars = charset || DataGenerator.CHARS_LOWER + DataGenerator.CHARS_UPPER;
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    /**
     * Generate a random email address
     */
    static randomEmail(domain?: string): string {
        const localPart = this.randomString(10).toLowerCase();
        const emailDomain = domain || 'test.example.com';
        return `${localPart}@${emailDomain}`;
    }

    /**
     * Generate a random phone number
     */
    static randomPhone(format?: string): string {
        const formatStr = format || '(###) ###-####';
        return formatStr.replace(/#/g, () => 
            Math.floor(Math.random() * 10).toString()
        );
    }

    /**
     * Generate a random integer between min and max (inclusive)
     */
    static randomInt(min: number, max: number): number {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    /**
     * Generate a random float between min and max
     */
    static randomFloat(min: number, max: number, decimals: number = 2): number {
        const value = Math.random() * (max - min) + min;
        return parseFloat(value.toFixed(decimals));
    }

    /**
     * Generate a random boolean
     */
    static randomBoolean(): boolean {
        return Math.random() >= 0.5;
    }

    /**
     * Generate a random date between two dates
     */
    static randomDate(start: Date, end: Date): Date {
        const startTime = start.getTime();
        const endTime = end.getTime();
        const randomTime = Math.random() * (endTime - startTime) + startTime;
        return new Date(randomTime);
    }

    /**
     * Generate a random UUID
     */
    static randomUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }

    /**
     * Generate a random password with specified requirements
     */
    static randomPassword(options?: {
        length?: number;
        includeUppercase?: boolean;
        includeLowercase?: boolean;
        includeNumbers?: boolean;
        includeSpecial?: boolean;
    }): string {
        const {
            length = 12,
            includeUppercase = true,
            includeLowercase = true,
            includeNumbers = true,
            includeSpecial = true,
        } = options || {};

        let charset = '';
        let password = '';

        if (includeLowercase) {
            charset += this.CHARS_LOWER;
            password += this.CHARS_LOWER.charAt(Math.floor(Math.random() * this.CHARS_LOWER.length));
        }
        if (includeUppercase) {
            charset += this.CHARS_UPPER;
            password += this.CHARS_UPPER.charAt(Math.floor(Math.random() * this.CHARS_UPPER.length));
        }
        if (includeNumbers) {
            charset += this.CHARS_NUMERIC;
            password += this.CHARS_NUMERIC.charAt(Math.floor(Math.random() * this.CHARS_NUMERIC.length));
        }
        if (includeSpecial) {
            charset += this.CHARS_SPECIAL;
            password += this.CHARS_SPECIAL.charAt(Math.floor(Math.random() * this.CHARS_SPECIAL.length));
        }

        // Fill remaining length with random characters
        while (password.length < length) {
            password += charset.charAt(Math.floor(Math.random() * charset.length));
        }

        // Shuffle the password
        return password.split('').sort(() => Math.random() - 0.5).join('');
    }

    /**
     * Generate a random first name
     */
    static randomFirstName(): string {
        const firstNames = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'James', 'Emma', 'Robert', 'Olivia'];
        return firstNames[Math.floor(Math.random() * firstNames.length)];
    }

    /**
     * Generate a random last name
     */
    static randomLastName(): string {
        const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Moore'];
        return lastNames[Math.floor(Math.random() * lastNames.length)];
    }

    /**
     * Generate a random full name
     */
    static randomFullName(): string {
        return `${this.randomFirstName()} ${this.randomLastName()}`;
    }

    /**
     * Pick a random element from an array
     */
    static randomElement<T>(array: T[]): T {
        return array[Math.floor(Math.random() * array.length)];
    }

    /**
     * Generate a random address
     */
    static randomAddress(): { street: string; city: string; state: string; zip: string } {
        const streets = ['Main St', 'Oak Ave', 'Park Blvd', 'Cedar Ln', 'Elm St'];
        const cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'];
        const states = ['NY', 'CA', 'IL', 'TX', 'AZ'];
        
        return {
            street: `${this.randomInt(100, 9999)} ${this.randomElement(streets)}`,
            city: this.randomElement(cities),
            state: this.randomElement(states),
            zip: this.randomInt(10000, 99999).toString(),
        };
    }
}

