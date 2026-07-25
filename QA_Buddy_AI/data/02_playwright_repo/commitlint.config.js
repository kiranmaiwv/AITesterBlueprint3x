/**
 * Commitlint Configuration
 * Enforces conventional commit message format
 * 
 * Format: type(scope): description
 * 
 * Examples:
 *   feat(login): add remember me functionality
 *   fix(checkout): resolve promo code validation
 *   test(product): add wishlist test cases
 *   refactor(pages): extract common locators
 *   docs(readme): update architecture section
 *   chore(deps): update playwright to v1.40
 * 
 * @author Pramod Dutta
 * @website https://thetestingacademy.com
 */

module.exports = {
    extends: ['@commitlint/config-conventional'],
    rules: {
        // Type must be one of the following
        'type-enum': [
            2,
            'always',
            [
                'feat',     // New feature
                'fix',      // Bug fix
                'docs',     // Documentation only
                'style',    // Code style (formatting, semicolons, etc.)
                'refactor', // Code refactoring
                'perf',     // Performance improvement
                'test',     // Adding or updating tests
                'build',    // Build system or external dependencies
                'ci',       // CI/CD configuration
                'chore',    // Other changes (tooling, etc.)
                'revert',   // Revert a previous commit
            ],
        ],
        // Type must be lowercase
        'type-case': [2, 'always', 'lower-case'],
        // Type cannot be empty
        'type-empty': [2, 'never'],
        // Subject cannot be empty
        'subject-empty': [2, 'never'],
        // Subject must not end with period
        'subject-full-stop': [2, 'never', '.'],
        // Header max length
        'header-max-length': [2, 'always', 100],
        // Body max line length
        'body-max-line-length': [2, 'always', 200],
    },
};

