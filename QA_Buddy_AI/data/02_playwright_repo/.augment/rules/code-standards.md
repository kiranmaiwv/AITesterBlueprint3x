# Code Standards & Best Practices

## Overview
This document defines coding standards for the Playwright Test Automation Framework.

---

## 🚫 Common Mistakes to Avoid

### 1. Locators in Modules
```typescript
// ❌ WRONG - Module should NOT have locators
export class LoginModule {
    async login() {
        await this.page.locator('#username').fill('user');  // BAD!
    }
}

// ✅ CORRECT - Use Page class methods
export class LoginModule {
    async login() {
        await this.loginPage.fillUsername('user');  // GOOD!
    }
}
```

### 2. Business Logic in Pages
```typescript
// ❌ WRONG - Page should NOT have logic
export class LoginPage {
    async login(user: string, pass: string) {
        if (user.includes('@')) {  // BAD! No conditionals
            await this.emailInput().fill(user);
        }
    }
}

// ✅ CORRECT - Keep pages simple
export class LoginPage {
    async fillUsername(user: string) {
        await this.usernameInput().fill(user);  // GOOD! Simple action
    }
}
```

### 3. Missing test.step()
```typescript
// ❌ WRONG - No step tracking
test('login test', async () => {
    await loginModule.doLogin('user', 'pass');
    await productModule.addToCart('item1');
});

// ✅ CORRECT - Use test.step for reporting
test('login test', async () => {
    await test.step('Login as user', async () => {
        await loginModule.doLogin('user', 'pass');
    });
    await test.step('Add item to cart', async () => {
        await productModule.addToCart('item1');
    });
});
```

### 4. Duplicate Page Objects
```typescript
// ❌ WRONG - Creating duplicate page instances
test('example', async ({ page }) => {
    const loginPage1 = new LoginPage(page);
    const loginPage2 = new LoginPage(page);  // BAD! Duplicate
});

// ✅ CORRECT - Use fixtures
test('example', async ({ loginPage }) => {
    // loginPage is provided by fixture - single instance
    await loginPage.navigate();
});
```

### 5. Hardcoded Waits
```typescript
// ❌ WRONG - Never use fixed timeouts
await page.waitForTimeout(5000);  // BAD!

// ✅ CORRECT - Use explicit waits
await page.waitForSelector('.element');  // GOOD!
await expect(element).toBeVisible();     // GOOD!
```

---

## ✅ Code Review Checklist

### Page Class
- [ ] Locators defined as arrow functions
- [ ] No business logic or conditionals
- [ ] Private page property in constructor
- [ ] Named exports only (no default)
- [ ] Single responsibility per method
- [ ] JSDoc comments for public methods

### Module Class
- [ ] Uses Page class methods only
- [ ] No direct locator access
- [ ] Business logic centralized here
- [ ] Logger used for step tracking
- [ ] Async/await pattern throughout
- [ ] Proper error handling

### Test Spec
- [ ] Uses test.describe() for grouping
- [ ] Tags present (@P0, @Feature)
- [ ] test.step() for important actions
- [ ] beforeEach/afterEach when needed
- [ ] Screenshots attached on failure
- [ ] Proper cleanup in afterEach

### General
- [ ] File in correct folder location
- [ ] Uses path aliases (@pages/, @modules/)
- [ ] No hardcoded values (use config/testdata)
- [ ] JSDoc comments present
- [ ] No console.log statements
- [ ] TypeScript types used properly

---

## 📋 ESLint Rules (Recommended)

```json
{
    "rules": {
        "no-console": "error",
        "@typescript-eslint/explicit-function-return-type": "warn",
        "@typescript-eslint/no-explicit-any": "error",
        "prefer-const": "error",
        "no-unused-vars": "error"
    }
}
```

---

## 🏷️ Test Tags Convention

| Tag | Usage | Example |
|-----|-------|---------|
| `@P0` | Critical priority | `@P0 @Login` |
| `@P1` | High priority | `@P1 @Checkout` |
| `@P2` | Medium priority | `@P2 @Search` |
| `@Smoke` | Smoke tests | `@Smoke @P0` |
| `@Regression` | Full regression | `@Regression` |
| `@Feature` | Feature name | `@Login @Product` |

---

## 📝 Commit Message Format

```
type(scope): description

feat(login): add remember me functionality
fix(checkout): resolve promo code validation
test(product): add wishlist test cases
refactor(pages): extract common locators
docs(readme): update architecture section
```

Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`

