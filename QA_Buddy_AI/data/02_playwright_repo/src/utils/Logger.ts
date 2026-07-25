export enum LogLevel {
    DEBUG = 'DEBUG',
    INFO = 'INFO',
    WARN = 'WARN',
    ERROR = 'ERROR',
}

export class Logger {
    private context: string;
    private static logLevel: LogLevel = LogLevel.INFO;

    constructor(context: string) {
        this.context = context;
    }

    /**
     * Create a new Logger instance with the given context
     */
    static create(context: string): Logger {
        return new Logger(context);
    }

    /**
     * Set the global log level
     */
    static setLogLevel(level: LogLevel): void {
        Logger.logLevel = level;
    }

    /**
     * Get the current log level
     */
    static getLogLevel(): LogLevel {
        return Logger.logLevel;
    }

    private formatMessage(level: LogLevel, message: string): string {
        return `[${new Date().toISOString()}] [${level}] [${this.context}] ${message}`;
    }

    private shouldLog(level: LogLevel): boolean {
        const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
        return levels.indexOf(level) >= levels.indexOf(Logger.logLevel);
    }

    /**
     * Log a debug message
     */
    debug(message: string): void {
        if (this.shouldLog(LogLevel.DEBUG)) {
            console.debug(this.formatMessage(LogLevel.DEBUG, message));
        }
    }

    /**
     * Log an info message
     */
    info(message: string): void {
        if (this.shouldLog(LogLevel.INFO)) {
            console.info(this.formatMessage(LogLevel.INFO, message));
        }
    }

    /**
     * Log a warning message
     */
    warn(message: string): void {
        if (this.shouldLog(LogLevel.WARN)) {
            console.warn(this.formatMessage(LogLevel.WARN, message));
        }
    }

    /**
     * Log an error message
     */
    error(message: string, error?: unknown): void {
        if (this.shouldLog(LogLevel.ERROR)) {
            console.error(this.formatMessage(LogLevel.ERROR, message), error || '');
        }
    }

    /**
     * Log a test step
     */
    step(stepNumber: number, description: string): void {
        this.info(`Step ${stepNumber}: ${description}`);
    }

    /**
     * Log the start of a test
     */
    testStart(testName: string): void {
        this.info(`========== START: ${testName} ==========`);
    }

    /**
     * Log the end of a test
     */
    testEnd(testName: string): void {
        this.info(`========== END: ${testName} ==========`);
    }
}

